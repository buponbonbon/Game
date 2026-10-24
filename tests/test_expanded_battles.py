"""Regression coverage for longer fields and the finite lane rescue system."""
import unittest
from pathlib import Path

from game.content import ENEMIES, HEROES, STAGES, catalog
from game.engine import Battle, STEP


class ExpandedBattleTests(unittest.TestCase):
    def test_longer_authored_waves_preserve_roster_and_final_boss(self):
        self.assertEqual(len(HEROES), 8)
        self.assertEqual(len(STAGES), 9)
        for stage in STAGES.values():
            self.assertGreaterEqual(len(stage['waves']), 12)
            self.assertGreaterEqual(stage['enemy_count'], 23)
            self.assertGreaterEqual(stage['waves'][-1]['at'], 170)
            if stage['boss']:
                self.assertEqual(stage['waves'][-1]['spawns'][0]['type'], stage['boss'])

    def test_expanded_deployment_and_guardian_column_are_authoritative(self):
        battle = Battle('wharf-1')
        result = battle.command(dict(action='place', hero='sword', lane=2, col=9))
        self.assertTrue(result['ok'])
        self.assertEqual(battle.qi, 75)
        result = battle.command(dict(action='place', hero='gatherer', lane=2, col=0))
        self.assertFalse(result['ok'])
        self.assertIn('guardian', result['message'].lower())
        self.assertEqual(battle.qi, 75)
        self.assertFalse(battle.command(dict(action='place', hero='gatherer', lane=2, col=10))['ok'])
        self.assertEqual(catalog()['rules']['columns'], 12)

    def test_guardian_sweeps_once_and_next_breach_costs_a_seal(self):
        battle = Battle('wharf-1')
        battle._spawn('tide', 2, .9)
        battle._spawn('yaksha', 2, 3)
        battle.advance(2)
        self.assertEqual(battle.kills, 2)
        self.assertEqual(battle.gate, 3)
        self.assertEqual(battle.defenses[2]['status'], 'spent')
        battle._spawn('tide', 2, .5001)
        battle.advance(STEP)
        self.assertEqual(battle.gate, 2)
        self.assertEqual(battle.defenses[2]['status'], 'spent')
        self.assertEqual(sum(e['kind'] == 'guardian' for e in battle.events), 1)

    def test_pause_freezes_guardian_and_other_lanes_keep_their_charge(self):
        battle = Battle('wharf-1')
        battle._spawn('tide', 1, .9)
        battle.advance(STEP)
        battle.command(dict(action='pause', paused=True))
        before = battle.snapshot()
        battle.advance(20)
        self.assertEqual(battle.snapshot(), before)
        self.assertEqual(battle.defenses[0]['status'], 'ready')

    def test_guardian_hits_a_boss_once_without_skipping_phases(self):
        battle = Battle('wharf-3')
        boss = battle._spawn('riverlord', 2, .9)
        battle.advance(2)
        self.assertIn(boss['id'], battle.enemies)
        self.assertEqual(boss['phase'], 2)
        self.assertEqual(battle.gate, 3)
        self.assertGreater(boss['x'], 1)

    def test_archive_uses_actual_stats_and_named_special_behaviors(self):
        entries = catalog()['enemies']
        self.assertEqual(len(entries), len(ENEMIES))
        for enemy in entries:
            self.assertTrue(enemy['abilities'][0]['name'])
            self.assertTrue(enemy['abilities'][0]['description'])
            self.assertTrue(enemy['counterplay'])
            for key in ('hp', 'armor', 'damage', 'speed', 'interval', 'resistances'):
                self.assertEqual(enemy[key], ENEMIES[enemy['id']][key])

    def test_readable_font_is_bundled_with_its_license(self):
        fonts = Path(__file__).resolve().parents[1] / 'web' / 'assets' / 'fonts'
        self.assertEqual((fonts / 'VT323-Regular.ttf').read_bytes()[:4], b'\x00\x01\x00\x00')
        self.assertIn('SIL OPEN FONT LICENSE', (fonts / 'OFL.txt').read_text())
