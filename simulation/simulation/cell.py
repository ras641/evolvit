import threading
import random
import math
import simulation.config as config


class Cell:

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.creatures = []
        self.food = []
        self.lock = threading.RLock()
        #print(f"🧱 Created Cell({x}, {y})")

    def add(self, obj):
        from .creatures import Creature
            # ✅ Lazy import to avoid circular import
        from .food import Food
        with self.lock:
            if isinstance(obj, Creature):
                self.creatures.append(obj)
                obj.cell = self
            elif isinstance(obj, Food):
                self.food.append(obj)
                obj.cell = self

    def remove(self, obj):
        from .creatures import Creature
        # ✅ Lazy import to avoid circular import
        from .food import Food
        with self.lock:
            try:
                if isinstance(obj, Creature):
                    self.creatures.remove(obj)
                    obj.cell = None
                elif isinstance(obj, Food):
                    self.food.remove(obj)
                    obj.cell = None
            except ValueError:
                pass

    def add_food(self):
        
        from .food import Food

        self.food.append(Food(position=[random.randint(0, 499), random.randint(0, 499)]))

    def run_creatures(self):
        """Handles all creature updates in one place."""
        
        with self.lock:

            for creature in self.creatures:
                if creature.isAlive:
                    creature.age += 1
                    creature.run_organs()

                    offspring = creature.reproduce()
                    if offspring and offspring.isAlive:
                        #offspring.sprite_id = offspring.compute_sprite_id()
                        self.add(offspring)
                    
                    creature.update_position()




    def run_collisions(self, apply_momentum=False):
        """Handles all creature and organ collisions, applying scaled push forces and optionally momentum transfer."""

        BASE_REPULSION_FORCE = 40
        MAX_REPULSION_FORCE = 80

        with self.lock:
            local_creatures = self.creatures[:]  # shallow copy

        for i, creature in enumerate(local_creatures):
            body_a = [
                creature.position[0] + creature.body_pos[0],
                creature.position[1] + creature.body_pos[1]
            ]

            for j in range(i + 1, len(local_creatures)):
                other = local_creatures[j]
                body_b = [
                    other.position[0] + other.body_pos[0],
                    other.position[1] + other.body_pos[1]
                ]

                # 1️⃣ Body-to-Body Collision
                dx = body_b[0] - body_a[0]
                dy = body_b[1] - body_a[1]
                distance = math.hypot(dx, dy)
                min_distance = config.BODY_RADIUS * 2
                overlap = max(0, min_distance * 1.05 - distance)

                if overlap > 0:
                    contact_point = [(body_a[0] + body_b[0]) / 2, (body_a[1] + body_b[1]) / 2]
                    repulsion_force = min(BASE_REPULSION_FORCE + overlap * 2, MAX_REPULSION_FORCE)
                    force_direction = math.atan2(dy, dx)

                    creature.apply_force(force_direction + math.pi, repulsion_force, contact_point)
                    other.apply_force(force_direction, repulsion_force, contact_point)

                # 2️⃣ Organ-to-Organ Collision
                for organ_a in creature.organs:
                    if not organ_a.isAlive: continue
                    pos_a = organ_a.get_absolute_position()

                    for organ_b in other.organs:
                        if not organ_b.isAlive: continue
                        pos_b = organ_b.get_absolute_position()

                        dx = pos_b[0] - pos_a[0]
                        dy = pos_b[1] - pos_a[1]
                        distance = math.hypot(dx, dy)
                        min_distance = organ_a.size + organ_b.size
                        overlap = max(0, min_distance - distance)

                        if overlap > 0:
                            contact_point = [(pos_a[0] + pos_b[0]) / 2, (pos_a[1] + pos_b[1]) / 2]
                            repulsion_force = min(BASE_REPULSION_FORCE + overlap * 2, MAX_REPULSION_FORCE)
                            force_direction = math.atan2(dy, dx)

                            creature.apply_force(force_direction + math.pi, repulsion_force, contact_point)
                            other.apply_force(force_direction, repulsion_force, contact_point)

                            # 🧠 Spike Damage Check
                            if organ_a.type == "spike" and organ_b.type != "spike":
                                organ_b.die()

                            if organ_b.type == "spike" and organ_a.type != "spike":
                                organ_a.die()

                # 3️⃣ Other’s Organ vs Creature Body
                for organ in other.organs:
                    if not organ.isAlive: continue
                    pos_organ = organ.get_absolute_position()

                    dx = body_a[0] - pos_organ[0]
                    dy = body_a[1] - pos_organ[1]
                    distance = math.hypot(dx, dy)
                    min_distance = config.BODY_RADIUS + organ.size * 1.1
                    overlap = max(0, min_distance - distance)

                    if overlap > 0:
                        contact_point = [(body_a[0] + pos_organ[0]) / 2, (body_a[1] + pos_organ[1]) / 2]
                        repulsion_force = min(BASE_REPULSION_FORCE + overlap * 2, MAX_REPULSION_FORCE)
                        force_direction = math.atan2(dy, dx)

                        other.apply_force(force_direction + math.pi, repulsion_force, contact_point)
                        creature.apply_force(force_direction, repulsion_force, contact_point)

                        # 💀 Spike vs Body
                        if organ.type == "spike":
                            if config.PRINT: print(f"creature {i} spiked by creature {j}")
                            
                            creature.die()

                # 4️⃣ Creature’s Organ vs Other Body
                for organ in creature.organs:
                    if not organ.isAlive: continue
                    pos_organ = organ.get_absolute_position()

                    dx = body_b[0] - pos_organ[0]
                    dy = body_b[1] - pos_organ[1]
                    distance = math.hypot(dx, dy)
                    min_distance = config.BODY_RADIUS + organ.size * 1.1
                    overlap = max(0, min_distance - distance)

                    if overlap > 0:
                        contact_point = [(body_b[0] + pos_organ[0]) / 2, (body_b[1] + pos_organ[1]) / 2]
                        repulsion_force = min(BASE_REPULSION_FORCE + overlap * 2, MAX_REPULSION_FORCE)
                        force_direction = math.atan2(dy, dx)

                        creature.apply_force(force_direction + math.pi, repulsion_force, contact_point)
                        other.apply_force(force_direction, repulsion_force, contact_point)

            
                        # 💀 Spike vs Body
                        if organ.type == "spike":
                            if config.PRINT: print(f"creature {j} spiked by creature {i}")
                            
                            other.die()













    def print_info(self):

        print (f"Cell postion: [{self.x}, {self.y}]")

        print (f"{len(self.creatures)} Creatures")

        for creature in self.creatures:

            creature.print_info()