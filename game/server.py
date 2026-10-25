"""Python 3.10+ local HTTP server for the VAN DAO browser client."""

from __future__ import annotations

import json
import logging
import secrets
import threading
import time
import uuid
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit


VERSION = "1.5.0"
MAX_BODY_BYTES = 65_536
LOGGER = logging.getLogger(__name__)


def load_battle_type():
    from .engine import Battle

    return Battle


def load_catalog():
    from .content import catalog

    return catalog()


class CapacityError(RuntimeError):
    """All local battle slots are in use."""


@dataclass
class BattleRecord:
    battle: Any
    last_access: float = field(default_factory=time.monotonic)
    lock: threading.RLock = field(default_factory=threading.RLock)
    failed: bool = False
    claimed_profiles: dict = field(default_factory=dict)


class BattleStore:
    """Own live battles and advance them independently of browser frame rate."""

    def __init__(self, battle_factory=None, max_battles=20, idle_seconds=1_800):
        self.battle_factory = battle_factory
        self.max_battles = max_battles
        self.idle_seconds = idle_seconds
        self.records: dict[str, BattleRecord] = {}
        self.lock = threading.Lock()
        self.stopped = threading.Event()
        self.thread = threading.Thread(
            target=self._tick, name="van-dao-simulation", daemon=True
        )

    def start(self):
        self.thread.start()

    def close(self):
        self.stopped.set()
        if self.thread.is_alive():
            self.thread.join(timeout=2)

    def _prune(self, now):
        stale = [
            key
            for key, value in self.records.items()
            if now - value.last_access > self.idle_seconds
        ]
        for key in stale:
            del self.records[key]

    def create(self, options):
        stage = options.get("stage", "wharf-1")
        if not isinstance(stage, str) or not stage or len(stage) > 64:
            raise ValueError("Choose a valid campaign stage.")
        seed = options.get("seed", secrets.randbits(31))
        if (
            isinstance(seed, bool)
            or not isinstance(seed, int)
            or not -(2**63) <= seed < 2**63
        ):
            raise ValueError("Seed must be a 64-bit integer.")
        realm = options.get("realm", 0)
        if isinstance(realm, bool) or not isinstance(realm, int) or not 0 <= realm <= 3:
            raise ValueError("Realm must be an integer from 0 to 3.")
        paused = options.get("paused", False)
        if not isinstance(paused, bool):
            raise ValueError("Paused must be true or false.")
        upgrades = options.get("upgrades", {})
        if not isinstance(upgrades, dict) or len(upgrades) > 8:
            raise ValueError("Upgrades must map hero IDs to branch A or B.")
        from .rules import validate_upgrades

        upgrades = validate_upgrades(upgrades)
        with self.lock:
            self._prune(time.monotonic())
            if len(self.records) >= self.max_battles:
                finished = sorted(
                    (record.last_access, key)
                    for key, record in self.records.items()
                    if record.failed or record.battle.status != "playing"
                )
                for _, key in finished:
                    del self.records[key]
                    if len(self.records) < self.max_battles:
                        break
            if len(self.records) >= self.max_battles:
                raise CapacityError(
                    "Too many battles are open. Close an old game tab or restart the local server."
                )
            factory = self.battle_factory or load_battle_type()
            battle = factory(stage, seed=seed, upgrades=dict(upgrades), realm=realm)
            if options.get("consumable"):
                battle.apply_preparation(options["consumable"])
            if paused:
                battle.command({"action": "pause", "paused": True})
            record = BattleRecord(battle)
            battle_id = uuid.uuid4().hex
            self.records[battle_id] = record
        with record.lock:
            return battle_id, record.battle.snapshot()

    def get(self, battle_id):
        with self.lock:
            record = self.records.get(battle_id)
            if record is None:
                raise KeyError(
                    "Battle not found. Return to the campaign and start a new battle."
                )
            record.last_access = time.monotonic()
            return record

    def snapshot(self, battle_id):
        record = self.get(battle_id)
        with record.lock:
            if record.failed:
                raise RuntimeError(
                    "This battle stopped unexpectedly. Please start a new battle."
                )
            return record.battle.snapshot()

    def delete(self, battle_id):
        with self.lock:
            record = self.records.pop(battle_id, None)
            if record is None:
                raise KeyError("Battle not found. It may already have been closed.")
        # A ticker iteration may already hold a reference to this record.
        with record.lock:
            record.failed = True

    def command(self, battle_id, command):
        record = self.get(battle_id)
        with record.lock:
            if record.failed:
                raise RuntimeError(
                    "This battle stopped unexpectedly. Please start a new battle."
                )
            result = record.battle.command(command)
            if not isinstance(result, dict):
                raise RuntimeError("Invalid battle command response.")
            return {**result, "state": record.battle.snapshot()}

    def _tick(self):
        previous = time.monotonic()
        next_tick = previous
        while not self.stopped.is_set():
            now = time.monotonic()
            # Avoid a large catch-up burst after machine sleep or debugger pauses.
            elapsed = min(max(now - previous, 0.0), 0.25)
            previous = now
            with self.lock:
                self._prune(now)
                records = list(self.records.values())
            for record in records:
                with record.lock:
                    if record.failed or record.battle.status != "playing":
                        continue
                    try:
                        record.battle.advance(elapsed)
                    except Exception:
                        record.failed = True
                        LOGGER.exception("A battle simulation stopped unexpectedly")
            next_tick += 1 / 60
            if next_tick < now:
                next_tick = now
            self.stopped.wait(max(0.0, next_tick - time.monotonic()))


class GameHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, web_root, battle_factory=None, catalog_factory=None):
        self.web_root = Path(web_root).resolve()
        self.store = BattleStore(battle_factory=battle_factory)
        self.catalog_factory = catalog_factory or load_catalog
        super().__init__(address, GameRequestHandler)
        self.store.start()

    def server_close(self):
        self.store.close()
        super().server_close()


class GameRequestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "VanDao/1.0"
    sys_version = ""
    timeout = 10
    server: GameHTTPServer

    def log_message(self, fmt, *args):
        LOGGER.debug("HTTP %s", fmt % args)

    def _send_bytes(self, status, body, content_type, *, head=False):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header(
            "Cache-Control", "no-store" if self.path.startswith("/api/") else "no-cache"
        )
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        self.end_headers()
        if not head:
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

    def _json(self, status, value, *, head=False):
        body = json.dumps(
            value, ensure_ascii=False, allow_nan=False, separators=(",", ":")
        ).encode("utf-8")
        self._send_bytes(status, body, "application/json; charset=utf-8", head=head)

    def _error(self, status, message, *, head=False):
        self._json(
            status, {"ok": False, "error": message, "message": message}, head=head
        )

    def _path(self):
        return urlsplit(self.path).path

    def do_HEAD(self):
        self._get(head=True)

    def do_GET(self):
        self._get()

    def _get(self, *, head=False):
        path = self._path()
        try:
            if path == "/api/health":
                self._json(HTTPStatus.OK, {"ok": True, "version": VERSION}, head=head)
            elif path == "/api/catalog":
                self._json(HTTPStatus.OK, self.server.catalog_factory(), head=head)
            elif path.startswith("/api/battle/") and len(path.split("/")) == 4:
                battle_id = path.rsplit("/", 1)[1]
                self._json(
                    HTTPStatus.OK, self.server.store.snapshot(battle_id), head=head
                )
            elif path.startswith("/api/"):
                self._error(HTTPStatus.NOT_FOUND, "Unknown API route.", head=head)
            else:
                self._static(path, head=head)
        except KeyError as error:
            self._error(HTTPStatus.NOT_FOUND, str(error).strip("'"), head=head)
        except Exception:
            LOGGER.exception("A local HTTP request failed")
            self._error(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "The local game server could not complete this request.",
                head=head,
            )

    def _static(self, path, *, head=False):
        decoded = unquote(path)
        if "\x00" in decoded or "\\" in decoded:
            self._error(HTTPStatus.FORBIDDEN, "Invalid asset path.", head=head)
            return
        candidate = self.server.web_root / decoded.lstrip("/")
        if decoded.endswith("/"):
            candidate = candidate / "index.html"
        candidate = candidate.resolve()
        if not candidate.is_relative_to(self.server.web_root):
            self._error(
                HTTPStatus.FORBIDDEN, "Asset path leaves the game directory.", head=head
            )
            return
        if not candidate.is_file():
            self._error(HTTPStatus.NOT_FOUND, "Game asset not found.", head=head)
            return
        mime = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "text/javascript; charset=utf-8",
            ".json": "application/json; charset=utf-8",
            ".png": "image/png",
            ".ogg": "audio/ogg",
            ".wav": "audio/wav",
            ".mp3": "audio/mpeg",
            ".ico": "image/x-icon",
            ".ttf": "font/ttf",
            ".txt": "text/plain; charset=utf-8",
        }.get(candidate.suffix.lower(), "application/octet-stream")
        self._send_bytes(HTTPStatus.OK, candidate.read_bytes(), mime, head=head)

    def _same_origin(self):
        origin = self.headers.get("Origin")
        if not origin:
            return True
        try:
            parsed = urlsplit(origin)
            return (
                parsed.scheme == "http"
                and parsed.netloc.lower() == self.headers.get("Host", "").lower()
            )
        except ValueError:
            return False

    def _read_json(self):
        content_type = (
            self.headers.get("Content-Type", "").partition(";")[0].strip().lower()
        )
        if content_type != "application/json":
            raise ValueError("Send commands as application/json.")
        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            raise ValueError("A Content-Length header is required.")
        try:
            length = int(raw_length)
        except ValueError as error:
            raise ValueError("Invalid Content-Length header.") from error
        if length < 0:
            raise ValueError("Invalid Content-Length header.")
        if length > MAX_BODY_BYTES:
            raise OverflowError("Request body is too large.")
        try:
            value = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("Request body must contain valid JSON.") from error
        if not isinstance(value, dict):
            raise ValueError("Request body must be a JSON object.")
        return value

    def do_POST(self):
        if not self._same_origin():
            self.close_connection = True
            self._error(
                HTTPStatus.FORBIDDEN, "Cross-origin game commands are not allowed."
            )
            return
        try:
            body = self._read_json()
        except OverflowError as error:
            self.close_connection = True
            self._error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, str(error))
            return
        except ValueError as error:
            self.close_connection = True
            self._error(HTTPStatus.BAD_REQUEST, str(error))
            return
        path = self._path()
        try:
            if path == "/api/hero-preview":
                from .rules import hero_data, validate_upgrades
                from .content import HEROES

                upgrades = validate_upgrades(body.get("upgrades", {}))
                self._json(
                    HTTPStatus.OK,
                    {"heroes": [hero_data(id, upgrades.get(id)) for id in HEROES]},
                )
            elif path == "/api/estate":
                from . import estate

                action = body.get("action", "inspect")
                if action == "claim_battle":
                    battle_id = body.get("battle_id")
                    if not isinstance(battle_id, str):
                        raise ValueError("Choose a battle to record.")
                    record = self.server.store.get(battle_id)
                    with record.lock:
                        profile = estate.normalize_profile(body.get("profile"))
                        if profile["save_id"] in record.claimed_profiles:
                            if battle_id in profile["estate"]["ledger"]:
                                result = dict(
                                    ok=True,
                                    profile=profile,
                                    catalogue=estate.view(profile),
                                    duplicate=True,
                                    notice="Battle already recorded.",
                                    outcome=record.claimed_profiles[
                                        profile["save_id"]
                                    ].get("outcome"),
                                )
                            else:
                                # A lost HTTP response must not lose the reward. The receipt
                                # is replayed only until the client's save contains this ID.
                                result = record.claimed_profiles[profile["save_id"]]
                        else:
                            result = estate.settle(
                                profile, battle_id, record.battle.snapshot()
                            )
                            record.claimed_profiles[profile["save_id"]] = result
                else:
                    result = estate.act(
                        body.get("profile"),
                        action,
                        **{
                            k: v
                            for k, v in body.items()
                            if k not in ("profile", "action")
                        },
                    )
                self._json(HTTPStatus.OK, result)
            elif path == "/api/battle":
                profile = None
                if "profile" in body:
                    from . import estate

                    profile, item = estate.prepare(body["profile"])
                    body.update(
                        upgrades=profile["upgrades"],
                        realm=estate.realm(profile),
                        consumable=item,
                    )
                battle_id, state = self.server.store.create(body)
                result = {"battle_id": battle_id, "state": state}
                if profile is not None:
                    result["profile"] = profile
                self._json(HTTPStatus.CREATED, result)
            elif (
                path.startswith("/api/battle/")
                and path.endswith("/command")
                and len(path.split("/")) == 5
            ):
                battle_id = path.split("/")[3]
                self._json(HTTPStatus.OK, self.server.store.command(battle_id, body))
            else:
                self._error(HTTPStatus.NOT_FOUND, "Unknown API route.")
        except KeyError as error:
            self._error(HTTPStatus.NOT_FOUND, str(error).strip("'"))
        except ValueError as error:
            self._error(HTTPStatus.BAD_REQUEST, str(error))
        except CapacityError as error:
            self._error(HTTPStatus.SERVICE_UNAVAILABLE, str(error))
        except Exception:
            LOGGER.exception("A local game command failed")
            self._error(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "The local game server could not complete this command.",
            )

    def do_DELETE(self):
        if not self._same_origin():
            self.close_connection = True
            self._error(
                HTTPStatus.FORBIDDEN, "Cross-origin game commands are not allowed."
            )
            return
        if self.headers.get("Content-Length", "0") != "0" or self.headers.get(
            "Transfer-Encoding"
        ):
            self.close_connection = True
            self._error(
                HTTPStatus.BAD_REQUEST,
                "Closing a battle does not accept a request body.",
            )
            return
        path = self._path()
        if not path.startswith("/api/battle/") or len(path.split("/")) != 4:
            self._error(HTTPStatus.NOT_FOUND, "Unknown API route.")
            return
        try:
            self.server.store.delete(path.rsplit("/", 1)[1])
            self._json(HTTPStatus.OK, {"ok": True, "message": "Battle closed."})
        except KeyError as error:
            self._error(HTTPStatus.NOT_FOUND, str(error).strip("'"))


def create_server(
    host="127.0.0.1",
    port=0,
    web_root=None,
    *,
    battle_factory=None,
    catalog_factory=None,
):
    """Create a bound server with a running simulation clock; caller serves/closes it."""
    root = (
        Path(web_root)
        if web_root is not None
        else Path(__file__).resolve().parent.parent / "web"
    )
    return GameHTTPServer(
        (host, port),
        root,
        battle_factory=battle_factory,
        catalog_factory=catalog_factory,
    )
