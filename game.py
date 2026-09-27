import random

from player import Player
from zombie import Zombie


class Game:
    """Shared turn-based engine for the terminal and browser editions."""

    def __init__(self, name):
        self.player = Player(name.strip() or "Survivor")
        self.zombie = Zombie()
        self.scene_count = 0
        self.location = "street"
        self.visited_locations = set()
        self.last_action = None
        self.mode = "menu"
        self.outcome = None
        self.messages = [
            "The city has fallen silent. Somewhere in the dark, something is moving.",
            "Find supplies, choose your routes, and survive long enough to reach the river gate.",
        ]

    def description(self):
        scenes = {
            "dark_hallway": "A dark hallway stretches ahead, and the air feels colder the farther you go.",
            "locked_door": "A heavy metal door blocks the next room. The lock looks stubborn, but not impossible.",
            "zombie_encounter": "A zombie lurches from the shadows, and the alley is too narrow to run safely.",
            "medical_room": "A small medical room waits behind the door. The shelves still hold a few supplies.",
        }
        if self.location in scenes:
            return scenes[self.location]
        if self.player.has_item("flashlight") and self.scene_count > 1:
            return "The flashlight beam catches muddy footprints leading toward a maintenance room."
        if self.player.has_item("map") and "hospital" in self.visited_locations:
            return "The map points toward a hospital ward that looks more dangerous than before."
        if "hospital" in self.visited_locations:
            return "The hospital corridor feels familiar now, and the silence is worse than before."
        if self.scene_count > 2:
            return "The street is quieter than before, but the windows are full of movement."
        return random.choice([
            "You hear scraping behind a boarded-up shop.",
            "A rusted truck blocks the road. A backpack lies beside it.",
            "An abandoned apartment stairwell smells like damp concrete and old blood.",
            "A store window shows a glowing emergency sign, but something is moving inside.",
        ])

    def explore_options(self):
        has = self.player.has_item
        if self.location == "dark_hallway":
            options = [("flashlight_use", "Use the flashlight to inspect the hallway")] if has("flashlight") else []
            return options + [("backtrack", "Back away and search another route")]
        if self.location == "locked_door":
            options = [("try_door", "Try the door")]
            if has("keys"):
                options.append(("use_keys", "Use the keys on the locked door"))
            return options + [("look_around", "Look for another way around")]
        if self.location == "zombie_encounter":
            options = [("fight", "Fight the zombie")]
            if has("ammo"):
                options.append(("use_ammo", "Use ammo to drive the zombie back"))
            return options + [("run", "Run for cover")]
        if self.location == "medical_room":
            options = [("search_supplies", "Search the shelves")]
            if has("medkit") and self.player.health < self.player.max_health:
                options.append(("use_medkit", "Use the medkit"))
            return options
        options = [
            ("search", "Search the area and pick up supplies"),
            ("fight", "Fight the zombie"),
            ("sneak", "Sneak around the danger"),
            ("move", "Move to a new street"),
        ]
        if has("flashlight"):
            options.append(("flashlight", "Use the flashlight to inspect the dark hallway"))
        if has("map"):
            options.append(("map", "Follow the map to a safer route"))
        if "hospital" in self.visited_locations:
            options.append(("hospital", "Re-enter the hospital"))
        if self.last_action == "search":
            options.append(("recheck", "Recheck the last place you found something"))
        return options

    def options(self):
        if self.outcome:
            return []
        menus = {
            "menu": [("explore", "Explore"), ("rest", "Rest"), ("inventory", "View inventory"),
                     ("items", "Use an item"), ("quit", "Leave the city for another night")],
            "search": [("pouch", "Take the medical pouch"), ("toolbox", "Take the locked toolbox"),
                       ("back", "Leave the supplies")],
            "fight": [("legs", "Strike its legs"), ("head", "Go for the head"),
                      ("retreat", "Run for cover")],
            "sneak": [("hide", "Hide behind a crate"), ("tunnel", "Crawl into a service tunnel"),
                      ("back", "Back away")],
            "move": [("entrance", "Check the hospital entrance"), ("radio", "Follow the radio signal"),
                     ("back", "Stay on this street")],
            "ending": [("river", "Take the river gate and escape"),
                       ("basement", "Rush into the hospital basement and risk everything")],
        }
        if self.mode == "explore":
            return self.explore_options()
        if self.mode == "items":
            return [(item, f"Use {item}") for item in self.player.inventory] + [("back", "Back")]
        return menus[self.mode]

    def snapshot(self):
        prompts = {
            "menu": "What will you do?",
            "explore": "Choose your next move.",
            "search": "You cannot carry everything. What will you take?",
            "fight": "The zombie blocks your path.",
            "sneak": "Something is moving behind you.",
            "move": "A new street opens ahead.",
            "items": "Choose an item.",
            "ending": "One final choice.",
            "finished": "Your story ends here.",
        }
        return {
            "name": self.player.name,
            "health": self.player.health,
            "max_health": self.player.max_health,
            "scene": self.scene_count,
            "location": self.location.replace("_", " ").title(),
            "zombie_health": self.zombie.health if self.location == "zombie_encounter" else None,
            "inventory": [{"name": item, "description": self.player.item_descriptions[item]}
                          for item in self.player.inventory],
            "messages": list(self.messages),
            "prompt": prompts[self.mode],
            "options": [{"id": key, "label": label} for key, label in self.options()],
            "outcome": self.outcome,
        }

    def choose(self, action):
        if self.outcome:
            return self.snapshot()
        if action not in dict(self.options()):
            self.messages = ["Invalid choice. Please choose one of the available options."]
            return self.snapshot()
        self.messages = []
        if self.mode == "menu":
            self._menu(action)
        elif self.mode == "explore":
            self._explore(action)
        elif self.mode == "items":
            if action != "back":
                self.messages = [self.player.use_item(action)]
            self._resolve()
        elif self.mode == "ending":
            self._finish(
                "survived" if action == "river" else "lost",
                "You take the river gate and slip out into the dawn. The city fades behind you. You survived."
                if action == "river" else
                "You charge into the hospital basement. The darkness swallows the last of your light. You did not make it out.",
            )
        else:
            self._branch(action)
        return self.snapshot()

    def _menu(self, action):
        if action == "explore":
            self.scene_count += 1
            self.mode = "explore"
            self.messages = [self.description()]
        elif action == "rest":
            before = self.player.health
            self.player.heal(15)
            self.messages = [
                f"You rest against a wall and recover {self.player.health - before} health. You listen for movement."
            ]
        elif action == "inventory":
            self.messages = [self.player.show_inventory()]
        elif action == "items":
            if self.player.inventory:
                self.mode = "items"
            else:
                self.messages = ["You have nothing to use."]
        elif action == "quit":
            self._finish("quit", "You decide to leave the block for another night.")

    def _explore(self, action):
        self.last_action = action
        if action in ("search", "fight", "sneak", "move"):
            self.mode = action
            self.messages = [{
                "search": "You find a couple of loose objects in the debris.",
                "fight": "The zombie shambles closer, blocking your path.",
                "sneak": "You slip into a dim hallway and hear something moving behind you.",
                "move": "A hospital sign glows in the distance. A radio signal cuts through the static.",
            }[action]]
            if action == "fight":
                self.location = "zombie_encounter"
            return
        if action in ("backtrack", "look_around"):
            self.location = "street"
            self.messages = ["You find your way back to the street and look for another route."]
        elif action == "run":
            self._run()
        elif action in ("flashlight", "flashlight_use"):
            self.player.add_to_inventory("ammo")
            self.messages = ["The flashlight reveals a hidden cache of ammo. You tuck it into your bag."]
            if action == "flashlight_use":
                self.zombie = Zombie()
                self.location = "zombie_encounter"
                self.messages.append("A zombie steps into the beam. Deal with it before moving on.")
        elif action == "use_ammo":
            self.player.remove_from_inventory("ammo")
            self.messages = ["You fire into the shadows. The zombie recoils, giving you time to reach the street."]
            self.zombie = Zombie()
            self.location = "street"
        elif action == "try_door":
            self.messages = ["The door is locked. You need something that fits the keyhole."]
        elif action == "use_keys":
            self.player.remove_from_inventory("keys")
            self.location = "medical_room"
            self.messages = ["The keys fit. The door opens to a small medical room."]
        elif action in ("search_supplies", "hospital"):
            self.player.add_to_inventory("medkit")
            self.location = "street"
            self.messages = ["You search the medical cabinet and find a medkit. You return to the street."]
        elif action == "use_medkit":
            self.messages = [self.player.use_item("medkit")]
            self.location = "street"
        elif action == "map":
            self.player.add_to_inventory("keys")
            self.messages = ["The map leads to a safer route and a locked gate. A discarded key ring lies nearby."]
        elif action == "recheck":
            self.player.add_to_inventory("map")
            self.messages = ["You recheck the debris and find a torn map."]
        self._resolve()

    def _branch(self, action):
        if self.mode == "search":
            if action == "pouch":
                self.player.add_to_inventory("medkit")
                self.messages = ["You grab a medkit and tuck it into your bag."]
            elif action == "toolbox":
                self.player.add_to_inventory("keys")
                self.messages = ["The toolbox is jammed, but you manage to pocket a ring of keys."]
            else:
                self.messages = ["You leave the supplies and move on."]
        elif self.mode == "fight":
            if action == "retreat":
                self._run()
            else:
                damage = self.player.attack(self.zombie)
                self.messages = [f"You {'strike its legs' if action == 'legs' else 'swing for its head'} for {damage} damage."]
                if self.zombie.is_alive():
                    damage = self.zombie.attack(self.player)
                    self.messages.append(f"The zombie claws back, dealing {damage} damage.")
                else:
                    self.messages.append("The zombie drops to the ground. The street is clear.")
                    self.zombie = Zombie()
                    self.location = "street"
        elif self.mode == "sneak":
            if action == "hide":
                self.player.take_damage(5)
                self.messages = ["You stay still until the noise passes. The stress costs you 5 health."]
            elif action == "tunnel":
                self.player.add_to_inventory("flashlight")
                self.location = "dark_hallway"
                self.messages = ["The tunnel opens into a maintenance room. You find a flashlight and add it to your bag."]
            else:
                self.location = "street"
                self.messages = ["You back away and keep moving."]
        elif self.mode == "move":
            if action == "entrance":
                self.player.add_to_inventory("ammo")
                self.visited_locations.add("hospital")
                self.location = "locked_door"
                self.messages = ["The hospital doors are jammed. You find ammo by a supply-room window, but a locked door blocks the way inside."]
            elif action == "radio":
                self.player.add_to_inventory("map")
                self.location = "street"
                self.messages = ["The signal leads to a dead transmitter and a torn map. You take the map."]
            else:
                self.location = "street"
                self.messages = ["You decide not to risk the unknown."]
        self._resolve()

    def _run(self):
        self.player.take_damage(10)
        self.location = "street"
        self.zombie = Zombie()
        self.messages = ["You scramble for cover. A glancing blow costs 10 health, but you reach the street."]

    def _resolve(self):
        self.mode = "menu"
        if not self.player.is_alive():
            self._finish("lost", "Your strength gives out. The city goes dark. You did not survive.")
        elif (self.scene_count >= 2 and self.location == "street"
              and self.player.has_item("flashlight") and self.player.has_item("ammo")):
            self.mode = "ending"
            self.messages.extend([
                "The city finally grows quiet. You have enough supplies to survive the night.",
                "A final gate stands ahead, lit by the first pale light of dawn.",
            ])

    def _finish(self, outcome, message):
        self.outcome = outcome
        self.mode = "finished"
        self.messages.append(message)
