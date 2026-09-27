import json
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from game import Game
from main import main


class GameTests(unittest.TestCase):
    def setUp(self):
        self.game = Game("Sam")

    def choose(self, *actions):
        for action in actions:
            self.assertIn(action, dict(self.game.options()))
            self.game.choose(action)
        return self.game.snapshot()

    def reach_encounter(self):
        self.choose("explore", "sneak", "tunnel", "explore", "flashlight_use")

    def reach_ending(self):
        self.reach_encounter()
        for _ in range(3):
            self.choose("explore", "fight", "legs")
        self.assertEqual(self.game.mode, "ending")

    def test_snapshot_is_json_serializable(self):
        self.assertEqual(json.loads(json.dumps(self.game.snapshot()))["name"], "Sam")

    def test_blank_name_gets_survivor_name(self):
        self.assertEqual(Game("   ").player.name, "Survivor")

    def test_invalid_action_does_not_change_state(self):
        self.game.choose("not-an-option")
        self.assertEqual(self.game.scene_count, 0)
        self.assertEqual(self.game.mode, "menu")
        self.assertIn("Invalid choice", self.game.messages[0])

    def test_backtrack_returns_to_street(self):
        self.choose("explore", "sneak", "tunnel", "explore", "backtrack")
        self.assertEqual(self.game.location, "street")

    def test_look_around_returns_to_street(self):
        self.choose("explore", "move", "entrance", "explore", "look_around")
        self.assertEqual(self.game.location, "street")

    def test_successful_move_does_not_report_hesitation(self):
        state = self.choose("explore", "move", "radio")
        self.assertTrue(self.game.player.has_item("map"))
        self.assertFalse(any("hesitate" in message for message in state["messages"]))

    def test_keys_unlock_medical_room_and_are_consumed(self):
        self.choose("explore", "search", "toolbox", "explore", "move", "entrance",
                    "explore", "use_keys")
        self.assertEqual(self.game.location, "medical_room")
        self.assertFalse(self.game.player.has_item("keys"))
        self.choose("explore", "search_supplies")
        self.assertTrue(self.game.player.has_item("medkit"))
        self.assertEqual(self.game.location, "street")

    def test_locked_door_without_keys_keeps_options_available(self):
        self.choose("explore", "move", "entrance", "explore", "try_door")
        self.assertEqual(self.game.location, "locked_door")
        self.choose("explore")
        self.assertNotIn("use_keys", dict(self.game.options()))
        self.assertIn("look_around", dict(self.game.options()))

    def test_encounter_cannot_be_skipped_by_ending_condition(self):
        self.reach_encounter()
        self.assertEqual(self.game.mode, "menu")
        self.assertEqual(self.game.location, "zombie_encounter")
        self.assertIsNone(self.game.outcome)

    def test_combat_persists_enemy_health_and_clears_defeated_enemy(self):
        self.choose("explore", "fight", "legs")
        self.assertEqual(self.game.zombie.health, 40)
        self.assertEqual(self.game.player.health, 90)
        self.choose("explore", "fight", "head")
        self.assertEqual(self.game.zombie.health, 20)
        self.choose("explore", "fight", "legs")
        self.assertEqual(self.game.location, "street")
        self.assertEqual(self.game.player.health, 80)
        self.assertEqual(self.game.zombie.health, 60)

    def test_run_has_a_cost_and_clears_encounter(self):
        self.choose("explore", "fight", "retreat")
        self.assertEqual(self.game.location, "street")
        self.assertEqual(self.game.player.health, 90)

    def test_contextual_run_is_handled(self):
        self.reach_encounter()
        self.choose("explore", "run")
        self.assertEqual(self.game.location, "street")
        self.assertEqual(self.game.player.health, 90)

    def test_ammo_is_consumed_only_when_used_in_encounter(self):
        self.reach_encounter()
        self.choose("explore", "use_ammo")
        self.assertFalse(self.game.player.has_item("ammo"))
        self.assertEqual(self.game.location, "street")
        self.assertIsNone(self.game.outcome)
        self.choose("explore", "flashlight")
        self.assertEqual(self.game.mode, "ending")

    def test_death_takes_precedence_over_escape(self):
        self.reach_encounter()
        self.game.player.health = 10
        self.choose("explore", "run")
        self.assertEqual(self.game.outcome, "lost")
        self.assertEqual(self.game.player.health, 0)
        self.assertEqual(self.game.options(), [])

    def test_combat_death_reports_an_ending(self):
        self.game.player.health = 10
        self.choose("explore", "fight", "head")
        self.assertEqual(self.game.outcome, "lost")
        self.assertIn("did not survive", self.game.messages[-1])

    def test_rest_does_not_reuse_medkit_for_bonus_health(self):
        self.game.player.health = 50
        self.game.player.add_to_inventory("medkit")
        self.choose("rest")
        self.assertEqual(self.game.player.health, 65)
        self.assertTrue(self.game.player.has_item("medkit"))

    def test_rest_reports_actual_recovery(self):
        self.game.player.health = 95
        self.choose("rest")
        self.assertIn("recover 5 health", self.game.messages[0])

    def test_empty_inventory_and_item_menu(self):
        self.choose("items")
        self.assertEqual(self.game.mode, "menu")
        self.choose("inventory")
        self.assertIn("nothing", self.game.messages[0])
        self.game.player.add_to_inventory("medkit")
        self.game.player.health = 40
        self.choose("items", "medkit")
        self.assertEqual(self.game.player.health, 70)
        self.assertFalse(self.game.player.has_item("medkit"))

    def test_recheck_and_map_routes(self):
        self.choose("explore", "search", "pouch", "explore", "recheck",
                    "explore", "map")
        self.assertTrue(self.game.player.has_item("map"))
        self.assertTrue(self.game.player.has_item("keys"))

    def test_both_final_choices(self):
        for action, outcome in [("river", "survived"), ("basement", "lost")]:
            with self.subTest(action=action):
                self.game = Game("Sam")
                self.reach_ending()
                self.choose(action)
                self.assertEqual(self.game.outcome, outcome)
                self.assertEqual(self.game.options(), [])

    def test_invalid_final_choice_does_not_kill_player(self):
        self.reach_ending()
        self.game.choose("typo")
        self.assertEqual(self.game.mode, "ending")
        self.assertIsNone(self.game.outcome)

    def test_finished_game_cannot_be_changed(self):
        self.choose("quit")
        before = self.game.snapshot()
        self.game.choose("explore")
        self.assertEqual(self.game.snapshot(), before)

    def test_all_cancel_routes_return_to_menu(self):
        for branch in ("search", "sneak", "move"):
            with self.subTest(branch=branch):
                self.game = Game("Sam")
                self.choose("explore", branch, "back")
                self.assertEqual(self.game.mode, "menu")

    def test_cli_handles_end_of_input_at_every_prompt(self):
        inputs = [
            [],
            ["Sam"],
            ["Sam", "1"],
            ["Sam", "1", "1"],
            ["Sam", "1", "1", "1", "4"],
        ]
        for values in inputs:
            with self.subTest(values=values):
                output = StringIO()
                with patch("builtins.input", side_effect=[*values, EOFError]), redirect_stdout(output):
                    main()
                self.assertIn("session ended", output.getvalue())

    def test_cli_rejects_out_of_range_numbers(self):
        output = StringIO()
        with patch("builtins.input", side_effect=["Sam", "0", "999", "hello", "5"]), redirect_stdout(output):
            main()
        self.assertIn("Invalid choice", output.getvalue())
        self.assertIn("available choice", output.getvalue())
        self.assertIn("another night", output.getvalue())


if __name__ == "__main__":
    unittest.main()
