import unittest

from player import Player


class PlayerInventoryTests(unittest.TestCase):
    def test_medkit_heals_and_removes_from_inventory(self):
        player = Player("Sam")
        player.add_to_inventory("medkit")
        player.take_damage(20)

        message = player.use_item("medkit")

        self.assertIn("recover 20 health", message)
        self.assertEqual(player.health, 100)
        self.assertFalse(player.has_item("medkit"))

    def test_show_inventory_includes_descriptions(self):
        player = Player("Sam")
        player.add_to_inventory("flashlight")

        inventory_text = player.show_inventory()

        self.assertIn("flashlight", inventory_text)
        self.assertIn("lights the way", inventory_text)

    def test_full_health_does_not_waste_medkit(self):
        player = Player("Sam")
        player.add_to_inventory("medkit")
        self.assertIn("already full", player.use_item("medkit"))
        self.assertTrue(player.has_item("medkit"))

    def test_ammo_is_not_wasted_outside_encounter(self):
        player = Player("Sam")
        player.add_to_inventory("ammo")
        self.assertIn("during a zombie encounter", player.use_item("ammo"))
        self.assertTrue(player.has_item("ammo"))

    def test_health_stays_in_bounds(self):
        player = Player("Sam")
        player.take_damage(200)
        self.assertEqual(player.health, 0)
        self.assertFalse(player.is_alive())
        player.heal(200)
        self.assertEqual(player.health, 100)

    def test_inventory_is_unique_and_reset_clears_it(self):
        player = Player("Sam")
        player.add_to_inventory("map")
        player.add_to_inventory("map")
        self.assertEqual(player.inventory, ["map"])
        player.take_damage(30)
        player.reset()
        self.assertEqual(player.inventory, [])
        self.assertEqual(player.health, 100)


if __name__ == "__main__":
    unittest.main()
