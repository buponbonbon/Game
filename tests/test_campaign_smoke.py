"""Full authored encounters using only legal player commands."""

import unittest

from game.engine import Battle
from game.content import STAGES


def defend_tutorial(seed):
    battle = Battle("wharf-1", seed=seed)
    opening = (
        {"action": "place", "hero": "gatherer", "lane": 2, "col": 1},
        {"action": "place", "hero": "sword", "lane": 2, "col": 2},
    )
    for command in opening:
        if not battle.command(command)["ok"]:
            raise AssertionError("The taught opening must be affordable.")
    defended = {2}
    for _ in range(360 * 60):
        state = battle.snapshot()
        for deployment_time, lane in ((12, 1), (24, 3)):
            if state["time"] >= deployment_time and lane not in defended and state["qi"] >= 75:
                result = battle.command({"action": "place", "hero": "sword", "lane": lane, "col": 2})
                if result["ok"]:
                    defended.add(lane)
        if state["time"] >= 50 and state["qi"] >= 75 and state["cards"]["sword"] <= 0:
            for lane in (2,1,3):
                if not any(h["lane"]==lane and h["col"]==5 for h in state["heroes"]):
                    battle.command({"action":"place","hero":"sword","lane":lane,"col":5})
                    break
        battle.advance(1 / 60)
        if battle.status != "playing":
            return battle
    raise AssertionError("The tutorial did not finish within six simulation minutes.")


class CampaignPlayabilityTests(unittest.TestCase):
    def test_taught_opening_clears_the_authored_tutorial(self):
        for seed in (7, 47, 2026):
            with self.subTest(seed=seed):
                battle = defend_tutorial(seed)
                state = battle.snapshot()
                self.assertEqual(state["status"], "victory")
                self.assertEqual(state["gate"], 3)
                self.assertEqual(state["kills"], STAGES["wharf-1"]["enemy_count"])
                self.assertEqual(state["metrics"]["deaths"], 0)
                self.assertEqual(state["metrics"]["invalid"], 0)
                self.assertEqual(state["rewards"]["stones"], 45)
                self.assertGreaterEqual(state["metrics"]["qi"]["gatherer"], 100)
                # A finished encounter cannot keep producing Qi or rewards.
                battle.advance(30)
                self.assertEqual(battle.snapshot(), state)

    def test_undefended_loss_can_be_retried_as_a_fresh_encounter(self):
        lost = Battle("wharf-1", seed=47)
        for _ in range(240):
            lost.advance(1)
            if lost.status != "playing":
                break
        state = lost.snapshot()
        self.assertEqual(state["status"], "defeat")
        self.assertEqual(state["gate"], 0)
        self.assertFalse(state["rewards"])
        self.assertFalse(lost.command({"action": "place", "hero": "sword", "lane": 2, "col": 2})["ok"])
        retry = defend_tutorial(47)
        self.assertEqual(retry.status, "victory")
        self.assertEqual(retry.snapshot()["gate"], 3)


if __name__ == "__main__":
    unittest.main()
