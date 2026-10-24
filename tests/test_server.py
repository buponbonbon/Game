"""HTTP and lifecycle checks independent of renderer and combat balance."""

from __future__ import annotations

import http.client
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest

from game.server import BattleStore, CapacityError, MAX_BODY_BYTES, create_server


class TinyBattle:
    def __init__(self, stage_id, seed=1, upgrades=None, realm=0):
        if stage_id != "wharf-1":
            raise ValueError("Unknown stage.")
        self.stage = stage_id
        self.seed = seed
        self.status = "playing"
        self.elapsed = 0
        self.paused = False
        self.qi = 150

    def advance(self, elapsed):
        if not self.paused:
            self.elapsed += elapsed

    def snapshot(self):
        return {"stage": self.stage, "seed": self.seed, "time": self.elapsed, "qi": self.qi, "paused": self.paused, "status": self.status}

    def command(self, command):
        if command.get("action") == "pause":
            self.paused = bool(command.get("paused"))
            return {"ok": True, "message": "Paused" if self.paused else "Resumed"}
        return {"ok": False, "message": "Unknown command."}


class LocalServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.web_root = Path(cls.temporary.name) / "web"
        cls.web_root.mkdir()
        (cls.web_root / "index.html").write_text("<!doctype html><title>VAN DAO test</title>", encoding="utf-8")
        (cls.web_root / "test.js").write_text("window.testAsset = true;", encoding="utf-8")
        (Path(cls.temporary.name) / "private.txt").write_text("not a game asset", encoding="utf-8")
        cls.server = create_server(web_root=cls.web_root, battle_factory=TinyBattle, catalog_factory=lambda: {"version": "test", "heroes": []})
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.server.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)
        cls.temporary.cleanup()

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        chosen_headers = dict(headers or {})
        if isinstance(body, dict) or isinstance(body, list):
            body = json.dumps(body)
            chosen_headers.setdefault("Content-Type", "application/json")
        connection.request(method, path, body=body, headers=chosen_headers)
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        connection.close()
        return result

    def new_battle(self):
        status, _, body = self.request("POST", "/api/battle", {"stage": "wharf-1", "seed": 12})
        self.assertEqual(status, 201)
        return json.loads(body)

    def test_health_catalog_and_static_assets(self):
        status, _, body = self.request("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["ok"])
        status, _, body = self.request("GET", "/api/catalog")
        self.assertEqual(json.loads(body)["version"], "test")
        status, headers, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", headers["Content-Type"])
        self.assertIn(b"VAN DAO test", body)
        status, headers, _ = self.request("GET", "/test.js")
        self.assertEqual(status, 200)
        self.assertIn("javascript", headers["Content-Type"])

    def test_head_returns_length_without_body(self):
        status, headers, body = self.request("HEAD", "/api/health")
        self.assertEqual(status, 200)
        self.assertGreater(int(headers["Content-Length"]), 0)
        self.assertEqual(body, b"")

    def test_battle_ticks_and_pause_is_authoritative(self):
        created = self.new_battle()
        battle_id = created["battle_id"]
        status, _, body = self.request("GET", f"/api/battle/{battle_id}")
        self.assertEqual(status, 200)
        started = json.loads(body)["time"]
        deadline = time.monotonic() + 2
        record = self.server.store.get(battle_id)
        while time.monotonic() < deadline:
            with record.lock:
                if record.battle.elapsed > started + 0.02:
                    break
            time.sleep(0.01)
        status, _, body = self.request("POST", f"/api/battle/{battle_id}/command", {"action": "pause", "paused": True})
        paused = json.loads(body)
        self.assertEqual(status, 200)
        self.assertTrue(paused["ok"])
        self.assertGreater(paused["state"]["time"], started)
        frozen = paused["state"]["time"]
        # Directly advancing under the same record lock also respects pause.
        with record.lock:
            record.battle.advance(1)
            self.assertEqual(record.battle.elapsed, frozen)
        status, _, body = self.request("GET", f"/api/battle/{battle_id}")
        self.assertEqual(json.loads(body)["time"], frozen)

    def test_invalid_json_and_payload_types_are_rejected(self):
        status, _, body = self.request("POST", "/api/battle", "{", {"Content-Type": "application/json"})
        self.assertEqual(status, 400)
        self.assertIn("valid JSON", json.loads(body)["error"])
        status, _, _ = self.request("POST", "/api/battle", [])
        self.assertEqual(status, 400)
        status, _, _ = self.request("POST", "/api/battle", {"seed": True})
        self.assertEqual(status, 400)
        status, _, _ = self.request("POST", "/api/battle", {"upgrades": {"sword": "C"}})
        self.assertEqual(status, 400)

    def test_large_body_and_foreign_origin_are_rejected(self):
        status, _, _ = self.request("POST", "/api/battle", "x" * (MAX_BODY_BYTES + 1), {"Content-Type": "application/json"})
        self.assertEqual(status, 413)
        status, _, _ = self.request("POST", "/api/battle", {}, {"Origin": "https://unrelated.example"})
        self.assertEqual(status, 403)
        status, _, _ = self.request("POST", "/api/battle", {}, {"Origin": f"http://127.0.0.1:{self.port}"})
        self.assertEqual(status, 201)

    def test_missing_battle_unknown_stage_and_unknown_route(self):
        status, _, _ = self.request("GET", "/api/battle/missing")
        self.assertEqual(status, 404)
        status, _, _ = self.request("POST", "/api/battle", {"stage": "unknown"})
        self.assertEqual(status, 400)
        status, _, _ = self.request("GET", "/api/unknown")
        self.assertEqual(status, 404)

    def test_paths_cannot_escape_static_root(self):
        for path in ("/../private.txt", "/%2e%2e/private.txt", "/..%5cprivate.txt"):
            status, _, body = self.request("GET", path)
            self.assertEqual(status, 403, path)
            self.assertNotIn(b"not a game asset", body)

    def test_server_close_stops_background_clock(self):
        extra = create_server(web_root=self.web_root, battle_factory=TinyBattle)
        self.assertTrue(extra.store.thread.is_alive())
        extra.server_close()
        self.assertFalse(extra.store.thread.is_alive())

    def test_delete_closes_battle_and_rejects_foreign_origin(self):
        battle_id = self.new_battle()["battle_id"]
        path = f"/api/battle/{battle_id}"
        status, _, _ = self.request("DELETE", path, headers={"Origin": "https://unrelated.example"})
        self.assertEqual(status, 403)
        status, _, body = self.request("DELETE", path)
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["ok"])
        status, _, _ = self.request("GET", path)
        self.assertEqual(status, 404)
        status, _, _ = self.request("DELETE", path)
        self.assertEqual(status, 404)

    def test_capacity_reuses_finished_slot_without_evicting_active_battle(self):
        store = BattleStore(battle_factory=TinyBattle, max_battles=2)
        first_id, _ = store.create({})
        active_id, _ = store.create({})
        with self.assertRaises(CapacityError):
            store.create({})
        store.get(first_id).battle.status = "victory"
        replacement_id, _ = store.create({})
        self.assertEqual(set(store.records), {active_id, replacement_id})
        with self.assertRaises(KeyError):
            store.get(first_id)
        store.delete(active_id)
        next_id, _ = store.create({})
        self.assertEqual(set(store.records), {replacement_id, next_id})


if __name__ == "__main__":
    unittest.main()
