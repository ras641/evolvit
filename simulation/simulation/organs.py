import random
import math

from .food import food_lock, food

from config import *

class Organ:
    allowed_types = ["mouth", "eye", "flipper", "spike"]

    def __init__(self, position, size, parent=None):
        self.position = position
        self.size = size
        self.type = "generic"
        self.parent = parent
        self.isAlive = True

    def set_parent(self, creature):
        self.parent = creature

    def simulate(self):
        pass

    def mutate(self):
        self.position[0] += random.randint(-5, 5)
        self.position[1] += random.randint(-5, 5)
        self.size = max(1, self.size + random.randint(-3, 3))

    def create_organ(organ_type, position, size, parent=None):
        organ_classes = {
            "mouth": Mouth,
            "eye": Eye,
            "flipper": Flipper,
            "spike": Spike
        }
        organ = organ_classes[organ_type](position, size, parent)
        return organ
    
    def copy(self):
        """Return a copy of this organ without a parent (parent set later)."""
        return self.__class__(self.position[:], self.size)  # Make sure position is copied (new list)
    
    def copy_mutate(self):
        new_pos = [self.position[0] + random.randint(-2, 2),
                self.position[1] + random.randint(-2, 2)]
        new_size = max(1, self.size + random.randint(-1, 1))
        return self.__class__(new_pos, new_size)

    def get_absolute_position(self):
        """Calculate absolute position using parent's position and single-angle direction."""
        if not self.parent:
            raise ValueError("Organ has no parent creature assigned!")

        ox, oy = self.position  # Relative organ position

        # ✅ Convert parent's direction (radians) into cosine & sine values
        cos_theta = math.cos(self.parent.direction)
        sin_theta = math.sin(self.parent.direction)

        # ✅ Rotate the organ's position based on the parent's facing angle
        rotated_x = ox * cos_theta - oy * sin_theta
        rotated_y = ox * sin_theta + oy * cos_theta

        # ✅ Compute absolute world position
        abs_x = self.parent.position[0] + rotated_x
        abs_y = self.parent.position[1] + rotated_y

        return [abs_x, abs_y]
    
    def die(self):
        if not self.parent or not self.parent.isAlive:
            return

        self.isAlive = False

        self.parent.sprite_id = self.parent.compute_sprite_id()
        self.parent.mass = self.parent.calculate_mass()
        self.parent.com = self.parent.calculate_com()
        self.parent.rotational_inertia = self.parent.calculate_rotational_inertia()

        if PRINT: print(f"🩸 Organ {self.type} destroyed on Creature {self.parent.id}")

    def to_dict(self):
        return {"type": self.type, "position": self.position, "size": self.size}

# ----- Specific Organ Types -----
class Mouth(Organ):
    def __init__(self, position, size, parent=None):
        super().__init__(position, size, parent)
        self.type = "mouth"

    def simulate(self):
        """Try to eat any nearby food based on organ's position."""
        mouth_pos = self.get_absolute_position()

        with food_lock:  # ✅ Thread-safe food access
            for food_obj in food[:]:  # ✅ Safe copy of the list for iteration
                food_pos = food_obj.position
                distance = math.hypot(mouth_pos[0] - food_pos[0], mouth_pos[1] - food_pos[1])

                food_radius = 4  # ✅ Matches the JavaScript rendering logic
                if distance <= self.size + food_radius:  # ✅ Adjusted to include food's radius
                    self.parent.energy += 20  # ✅ Adjust energy gain as needed
                    food.remove(food_obj)  # ✅ Remove food from global list
                    if PRINT: print(f"🍽️ Creature {self.parent.id} ate food at {food_pos} (Energy: {self.parent.energy})")
                    #break  # ✅ Only eat one food per simulation frame

class Eye(Organ):
    def __init__(self, position, size, parent=None):
        super().__init__(position, size, parent)
        self.type = "eye"

class Flipper(Organ):
    def __init__(self, position, size, parent=None):
        super().__init__(position, size, parent)
        self.type = "flipper"

    def simulate(self):
        """Apply force in the direction the creature is facing (world space)."""
        if not self.parent:
            return  # Organ must be attached to a creature

        # ✅ Use absolute position of the flipper in world space
        world_position = self.get_absolute_position()

        # ✅ Apply force in the global frame using angle
        force_magnitude = self.size * 2  # Constant thrust force
        self.parent.apply_force(angle=self.parent.direction, magnitude=force_magnitude, world_position=world_position)

        # ✅ Apply energy cost per activation
        self.parent.energy -= (0.001 * self.size)  # Constant energy drain for using flippers



    

class Spike(Organ):
    def __init__(self, position, size, parent=None):
        super().__init__(position, size, parent)
        self.type = "spike"
    def simulate(self):
        """Try to eat any nearby food based on organ's position."""
        self.parent.energy -= (0.01 * self.size)
