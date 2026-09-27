class Zombie:
    def __init__(self, health=60, damage=10):
        self.health = health
        self.damage = damage

    def is_alive(self):
        return self.health > 0

    def take_damage(self, amount):
        self.health -= amount
        if self.health < 0:
            self.health = 0

    def attack(self, player):
        player.take_damage(self.damage)
        return self.damage

    def show_status(self):
        return f"Zombie Health: {self.health}, Damage: {self.damage}"
