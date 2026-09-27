class Player:
    def __init__(self, name):
        self.name = name
        self.health = 100
        self.max_health = 100
        self.inventory = []
        self.item_descriptions = {
            "medkit": "a first-aid medkit that restores health",
            "flashlight": "a flashlight that lights the way",
            "ammo": "a box of bullets for emergencies",
            "keys": "a ring of keys that may open locked doors",
            "map": "a torn map with a few useful routes marked"
        }

    def take_damage(self, amount):
        self.health -= amount
        if self.health < 0:
            self.health = 0

    def attack(self, zombie):
        damage = 20
        zombie.take_damage(damage)
        return damage

    def heal(self, amount):
        self.health += amount
        if self.health > self.max_health:
            self.health = self.max_health

    def is_alive(self):
        return self.health > 0

    def add_to_inventory(self, item):
        if item not in self.inventory:
            self.inventory.append(item)
        return self.inventory

    def remove_from_inventory(self, item):
        if item in self.inventory:
            self.inventory.remove(item)

    def has_item(self, item):
        return item in self.inventory

    def use_item(self, item):
        if item == "medkit":
            if self.has_item("medkit"):
                if self.health == self.max_health:
                    return "Your health is already full. Save the medkit for later."
                self.remove_from_inventory("medkit")
                before = self.health
                self.heal(30)
                return f"You use the medkit and recover {self.health - before} health."
            return "You do not have a medkit."

        if item == "flashlight":
            if self.has_item("flashlight"):
                return "The flashlight lights the way and helps you inspect dark areas."
            return "You do not have a flashlight."

        if item == "ammo":
            if self.has_item("ammo"):
                return "Keep the ammo ready. Choose 'Use ammo' during a zombie encounter to spend it."
            return "You do not have any ammo."

        if item == "keys":
            if self.has_item("keys"):
                return "The keys might open a locked door somewhere in the city."
            return "You do not have any keys."

        if item == "map":
            if self.has_item("map"):
                return "The map gives you a better sense of the routes around you."
            return "You do not have a map."

        return "That item cannot be used right now."

    def show_inventory(self):
        if not self.inventory:
            return "You are carrying nothing."

        lines = ["Inventory:"]
        for item in self.inventory:
            description = self.item_descriptions.get(item, item)
            lines.append(f"- {item}: {description}")
        return "\n".join(lines)

    def show_status(self):
        return f"Player: {self.name}, Health: {self.health}/{self.max_health}, Inventory: {self.inventory}"

    def reset(self):
        self.health = self.max_health
        self.inventory.clear()