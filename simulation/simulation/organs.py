import random
import math
from simulation.config import *


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

        # ✅ Calculate mass first
        self.parent.mass = self.parent.calculate_mass()

        old_body_pos = self.parent.body_pos[:]

        # ✅ Calculate center of mass (from organ layout)
        self.parent.body_pos = self.parent.calculate_com()

        # 🧠 After COM & organ shift, self.parent.body_pos is now updated to the *new* body offset

        # ✅ Compute how much the body shifted in local space
        dx = old_body_pos[0] - self.parent.body_pos[0]
        dy = old_body_pos[1] - self.parent.body_pos[1]

        # ✅ Move the whole creature so that the *body organ* stays in the same world spot
        self.parent.position[0] += dx
        self.parent.position[1] += dy

        # print (self.body_pos)

        # ✅ Shift all organ positions so COM is now origin
        for organ in self.parent.organs:
            if not organ.isAlive: continue
            organ.position[0] += self.parent.body_pos[0]
            organ.position[1] += self.parent.body_pos[1]

        # ✅ Since we centered organs around COM, update self.position to be world COM
        self.position[0] += self.parent.body_pos[0]
        self.position[1] += self.parent.body_pos[1]

        # ✅ Now recalculate rotational inertia (based on new COM-relative organ positions)
        self.parent.rotational_inertia = self.parent.calculate_rotational_inertia()

        # ✅ Sprite generation (after validation and adjustment)
        self.parent.sprite_id = self.parent.compute_sprite_id()

        with self.parent.cell.lock:

            delta = self.parent.cell.get_current_delta()

            delta["creatures"] += (
                f"o[{self.parent.id},{self.parent.sprite_id}],"
            )

        if PRINT: print(f"🩸 Organ {self.type} destroyed on Creature {self.parent.id}")

    def to_dict(self):
        return {"type": self.type, "position": self.position, "size": self.size}

# ----- Specific Organ Types -----
class Mouth(Organ):


    def __init__(self, position, size, parent=None):
        super().__init__(position, size, parent)
        self.type = "mouth"

    def simulate(self):
        #print(f"[Mouth] Simulating for Creature {self.parent.id if self.parent else '?'}")

        if not self.parent or not self.parent.cell:
            print("[Mouth] No parent or no cell")
            return
        
        if not self.isAlive or not self.parent.isAlive:
            return
        


        mouth_pos = self.get_absolute_position()
        #print(f"[Mouth] Position: {mouth_pos}")

        #print(f"[Mouth] Cell: {self.parent.cell}")
        #print(f"[Mouth] Cell type: {type(self.parent.cell)}")

        #print(f"[Mouth] Cell has lock? {'lock' in dir(self.parent.cell)}")

        cell = self.parent.cell

        try:
            with cell.lock:
                food_list = cell.food[:]
        except Exception as e:
            #print(f"[Mouth] Lock failed: {e}")
            return

        for food_obj in food_list:
            food_pos = food_obj.position
            dist = math.hypot(mouth_pos[0] - food_pos[0], mouth_pos[1] - food_pos[1])
            #print(f"[Mouth] Distance to food: {dist}")

            if dist <= self.size + 4:
                from simulation.config import frame_count
                try:
                    with cell.lock:
                        if food_obj in cell.food:

                            #delta = self.cell.get_current_delta(frame_count)
            
                            #delta["deleted_food"] += f"[{food_obj.position[0]},{food_obj.position[1]}],"
                            cell.remove(food_obj)

                            self.parent.change_energy(20)
                            #print(f"[Mouth] Ate food at {food_pos}")
                            #print (f"e[{self.parent.id}, {round(self.parent.energy)}],")
                    break
                except Exception as e:
                    print(f"[Mouth] Error removing food: {e}")

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
        
        if not self.isAlive:
            return

        # ✅ Use absolute position of the flipper in world space
        world_position = self.get_absolute_position()

        # ✅ Apply force in the global frame using angle
        force_magnitude = self.size * 0.5  # Constant thrust force
        self.parent.apply_force(angle=self.parent.direction, magnitude=force_magnitude, world_position=world_position)

        # ✅ Apply energy cost per activation
        self.parent.energy -= (0.001 * self.size)  # Constant energy drain for using flippers



    

class Spike(Organ):
    def __init__(self, position, size, parent=None):
        super().__init__(position, size, parent)
        self.type = "spike"
    def simulate(self):
        """Try to eat any nearby food based on organ's position."""
        self.parent.energy -= (0.001 * self.size)
