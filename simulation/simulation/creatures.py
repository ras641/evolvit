import random
import math
from .organs import Organ
import threading

import os

from simulation.config import *


sprite_lock = threading.Lock()


class Creature:

    ORGANS = ["mouth", "eye", "flipper", "spike"]
    MAX_ORGANS = 5
    counter = 0

    sprite_map = {}  # {sprite_id: serialized_organs}
    sprite_counter = 0  # For assigning unique sprite IDs
    sprite_lock = threading.Lock()

    creatures = []  # ✅ Static list for all creatures
    creatures_lock = threading.Lock()  # ✅ Thread-safe locking

    force_log = {}

    @classmethod
    def get_creature_count(cls):
        with cls.creatures_lock:
            return len(cls.creatures)

    @staticmethod
    def run_creatures():
        """Handles all creature updates in one place."""
        offspring_list = []
        
        with Creature.creatures_lock:

            for creature in Creature.creatures:
                if creature.isAlive:
                    creature.age += 1
                    creature.run_organs()
                    creature.update_position()

                    if creature.energy <= 0:
                        creature.die()

                    if REPRODUCE:
                        offspring = creature.reproduce()
                        if offspring:
                            offspring_list.append(offspring)

            # ✅ Add offspring and remove dead creatures
            Creature.creatures.extend(offspring_list)
            Creature.creatures[:] = [c for c in Creature.creatures if c.isAlive]

        # ✅ Run collisions after all movement is done
        Creature.run_collisions()

    @staticmethod
    def run_collisions(apply_momentum=False):
        """Handles all creature and organ collisions, applying scaled push forces and optionally momentum transfer."""

        BASE_REPULSION_FORCE = 20
        MAX_REPULSION_FORCE = 60

        creature_hits = set()
        organ_hits = set()

        for i, creature in enumerate(Creature.creatures):
            body_a = [
                creature.position[0] + creature.body_pos[0],
                creature.position[1] + creature.body_pos[1]
            ]

            for j in range(i + 1, len(Creature.creatures)):
                other = Creature.creatures[j]
                body_b = [
                    other.position[0] + other.body_pos[0],
                    other.position[1] + other.body_pos[1]
                ]

                # 1️⃣ Body-to-Body Collision
                dx = body_b[0] - body_a[0]
                dy = body_b[1] - body_a[1]
                distance = math.hypot(dx, dy)
                min_distance = BODY_RADIUS * 2
                overlap = max(0, min_distance * 1.05 - distance)

                if overlap > 0:
                    contact_point = [(body_a[0] + body_b[0]) / 2, (body_a[1] + body_b[1]) / 2]
                    repulsion_force = min(BASE_REPULSION_FORCE + overlap * 2, MAX_REPULSION_FORCE)
                    force_direction = math.atan2(dy, dx)

                    creature.apply_force(force_direction + math.pi, repulsion_force, contact_point)
                    other.apply_force(force_direction, repulsion_force, contact_point)

                    if apply_momentum:
                        Creature.resolve_momentum_transfer(creature, None, other, None, contact_point)

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

                            if apply_momentum:
                                Creature.resolve_momentum_transfer(creature, organ_a, other, organ_b, contact_point)

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
                    min_distance = BODY_RADIUS + organ.size * 1.1
                    overlap = max(0, min_distance - distance)

                    if overlap > 0:
                        contact_point = [(body_a[0] + pos_organ[0]) / 2, (body_a[1] + pos_organ[1]) / 2]
                        repulsion_force = min(BASE_REPULSION_FORCE + overlap * 2, MAX_REPULSION_FORCE)
                        force_direction = math.atan2(dy, dx)

                        other.apply_force(force_direction + math.pi, repulsion_force, contact_point)
                        creature.apply_force(force_direction, repulsion_force, contact_point)

                        # 💀 Spike vs Body
                        if organ.type == "spike":
                            if PRINT: print(f"creature {i} spiked by creature {j}")
                            
                            creature.die()

                # 4️⃣ Creature’s Organ vs Other Body
                for organ in creature.organs:
                    if not organ.isAlive: continue
                    pos_organ = organ.get_absolute_position()

                    dx = body_b[0] - pos_organ[0]
                    dy = body_b[1] - pos_organ[1]
                    distance = math.hypot(dx, dy)
                    min_distance = BODY_RADIUS + organ.size * 1.1
                    overlap = max(0, min_distance - distance)

                    if overlap > 0:
                        contact_point = [(body_b[0] + pos_organ[0]) / 2, (body_b[1] + pos_organ[1]) / 2]
                        repulsion_force = min(BASE_REPULSION_FORCE + overlap * 2, MAX_REPULSION_FORCE)
                        force_direction = math.atan2(dy, dx)

                        creature.apply_force(force_direction + math.pi, repulsion_force, contact_point)
                        other.apply_force(force_direction, repulsion_force, contact_point)

            
                        # 💀 Spike vs Body
                        if organ.type == "spike":
                            if PRINT: print(f"creature {j} spiked by creature {i}")
                            
                            other.die()



        # Return collision results
        return {
            "creature_hits": list(creature_hits),
            "organ_hits": list(organ_hits)
        }


    def resolve_momentum_transfer(creature_a, organ_a, creature_b, organ_b, contact_point):
        """Handles inelastic momentum transfer and adds a repulsive push force to prevent overlap."""

        # ✅ Assign mass based on whether it's a body or an organ
        mass_a = organ_a.size if organ_a else creature_a.mass  
        mass_b = organ_b.size if organ_b else creature_b.mass  

        # ✅ Compute velocity at the impact point
        velocity_a = Creature.get_velocity_at_point(creature_a, organ_a, contact_point)
        velocity_b = Creature.get_velocity_at_point(creature_b, organ_b, contact_point)

        # ✅ Compute velocity difference along impact direction
        vx_diff = velocity_b[0] - velocity_a[0]
        vy_diff = velocity_b[1] - velocity_a[1]

        # ✅ Compute impact normal
        dx = creature_b.position[0] - creature_a.position[0]
        dy = creature_b.position[1] - creature_a.position[1]
        distance = max(math.hypot(dx, dy), 1)  # Avoid division by zero

        normal_x = dx / distance
        normal_y = dy / distance

        # ✅ Compute relative velocity along impact normal
        relative_velocity = (vx_diff * normal_x) + (vy_diff * normal_y)

        if relative_velocity > 0:
            return  # ✅ No need to handle if they are already moving apart

        # ✅ Compute impulse magnitude (inelastic collision)
        elasticity = 0.001  # ✅ Lower value makes the collision highly inelastic (energy lost)
        impulse = (-(1 + elasticity) * relative_velocity) / (1 / mass_a + 1 / mass_b)

        # ✅ Convert impulse into force vectors
        force_x = impulse * normal_x
        force_y = impulse * normal_y

        # ✅ Apply force immediately at impact location
        creature_a.apply_force(math.atan2(-force_y, -force_x), abs(impulse / mass_a) * 30, contact_point)
        creature_b.apply_force(math.atan2(force_y, force_x), abs(impulse / mass_b) * 30, contact_point)

        # ✅ Approximate rotational effect (only if impact is far from center)
        center_distance_a = math.hypot(contact_point[0] - creature_a.position[0], contact_point[1] - creature_a.position[1])
        center_distance_b = math.hypot(contact_point[0] - creature_b.position[0], contact_point[1] - creature_b.position[1])

        TORQUE_SCALING = 0.0001  # ✅ Reduce torque influence even further

        if center_distance_a > 8:  # ✅ Apply only if impact isn't too close to center
            creature_a.angular_velocity += (impulse / mass_a) * (center_distance_a * TORQUE_SCALING)

        if center_distance_b > 8:
            creature_b.angular_velocity += (impulse / mass_b) * (center_distance_b * TORQUE_SCALING)

        # ✅ Apply repulsive force to push organs away from each other
        repulsion_magnitude = 2  # ✅ Tunable push strength
        creature_a.apply_force(math.atan2(-dy, -dx), repulsion_magnitude, contact_point)
        creature_b.apply_force(math.atan2(dy, dx), repulsion_magnitude, contact_point)



    def get_velocity_at_point(creature, organ, contact_point):
        """Approximates the velocity of an organ or body at a collision point, considering both linear and rotational movement."""

        # ✅ Get linear velocity of the creature
        vx = creature.velocity[0]
        vy = creature.velocity[1]

        if organ:
            # ✅ Compute relative position of organ to creature's center
            ox, oy = organ.position
            cx, cy = creature.position
            relative_x = ox - cx
            relative_y = oy - cy

            # ✅ Compute perpendicular velocity due to rotation
            rotation_vx = -relative_y * creature.angular_velocity
            rotation_vy = relative_x * creature.angular_velocity

            # ✅ Apply scaled rotation only if the impact point is far from the center
            distance_from_center = math.hypot(relative_x, relative_y)
            ROTATION_INFLUENCE = 0.5  # ✅ Reduce excessive spin influence
            if distance_from_center > 8:
                vx += rotation_vx * ROTATION_INFLUENCE
                vy += rotation_vy * ROTATION_INFLUENCE

        return [vx, vy]






    def __init__(self, position, mutation_rate=1.0, user_created=True, name=None, organs=None):
        self.id = Creature.counter
        Creature.counter += 1
        self.name = name if name else f"Creature_{self.id}"
        self.position = position[:]  # Now represents the center of mass
        self.energy = 50
        self.age = 0
        self.mutation_rate = mutation_rate
        self.user_created = user_created
        self.parent_ids = []
        self.generation = 0
        self.direction = 0  # radians
        self.isAlive = True
        self.organs = []
        from .world import world
        self.cell = world.cell_grid[0][0]

        self.velocity = [0, 0]
        self.angular_velocity = 0

        self.last_sent_x = self.position[0]
        self.last_sent_y = self.position[1]
        self.last_sent_direction = self.direction

        self.offspringcounter = 1

        # ---- Organ setup ----
        if organs:
            for organ_data in organs:
                if isinstance(organ_data, Organ):
                    organ = organ_data
                    organ.set_parent(self)
                elif isinstance(organ_data, dict):
                    organ_type = organ_data["type"]
                    position = organ_data["position"]
                    size = organ_data["size"]
                    organ = Organ.create_organ(organ_type, position, size, parent=self)
                else:
                    if PRINT: print(f"❌ Unknown organ format: {organ_data}")
                    continue
                self.organs.append(organ)

 


        # ✅ Calculate mass first
        self.mass = self.calculate_mass()

        # ✅ Calculate center of mass (from organ layout)
        self.body_pos = self.calculate_com()

        # print (self.body_pos)

        # ✅ Shift all organ positions so COM is now origin
        for organ in self.organs:
            if not organ.isAlive: continue
            organ.position[0] += self.body_pos[0]
            organ.position[1] += self.body_pos[1]

        # ✅ Since we centered organs around COM, update self.position to be world COM
        self.position[0] += self.body_pos[0]
        self.position[1] += self.body_pos[1]

        # ✅ Validate organ layout
        if not self.validate_organs():
            self.die()
            return

        # ✅ Now recalculate rotational inertia (based on new COM-relative organ positions)
        self.rotational_inertia = self.calculate_rotational_inertia()

        # ✅ Sprite generation (after validation and adjustment)
        self.sprite_id = self.compute_sprite_id()

        if PRINT:
            
            print(f"✅ Creature {self.id} created with {len(self.organs)} organs. Sprite ID: {self.sprite_id}")
            print(f"✅ body_pos: {self.body_pos}")

            for organ in self.organs:

                print(f"✅ organ_pos: {organ.position}")

    def print_info(self):
        print(f"\n📘 Creature Info: {self.name} (ID: {self.id})")
        print(f"├── Alive: {self.isAlive}")
        print(f"├── Position: {self.position}")
        print(f"├── Velocity: {self.velocity}")
        print(f"├── Angular Velocity: {self.angular_velocity}")
        print(f"├── Direction (radians): {self.direction}")
        print(f"├── Energy: {self.energy}")
        print(f"├── Age: {self.age}")
        print(f"├── Mass: {self.mass}")
        print(f"├── Rotational Inertia: {self.rotational_inertia}")
        print(f"├── Mutation Rate: {self.mutation_rate}")
        print(f"├── User Created: {self.user_created}")
        print(f"├── Generation: {self.generation}")
        print(f"├── Parent IDs: {self.parent_ids}")
        print(f"├── Sprite ID: {self.sprite_id}")
        print(f"├── Body COM Offset: {self.body_pos}")
        print(f"└── Organs ({len(self.organs)} total):")
        for i, organ in enumerate(self.organs):
            status = "Alive" if organ.isAlive else "Dead"
            print(f"    ├─ #{i}: {organ.__class__.__name__} | Pos: {organ.position} | Size: {organ.size} | {status}")

    def validate_organs(self):
        """Check if organs are within bounds, not overlapping the body or other organs."""

        for i, organ in enumerate(self.organs):
            
            if not organ.isAlive: continue
            x, y = organ.position
            size = organ.size

            # ✅ 1. Bounds check: inside design area (-50 to +50 relative to COM)
            if not (-50 + size <= x <= 50 - size) or not (-50 + size <= y <= 50 - size):
                if PRINT:
                    print(f"❌ {self.id}: Organ {organ.type} at {organ.position} is out of bounds.")
                return False

            # ✅ 2. Check overlap with body (at self.body_pos, radius = BODY_RADIUS)
            dx = x - self.body_pos[0]
            dy = y - self.body_pos[1]
            distance_to_body = math.hypot(dx, dy)
            if distance_to_body < (BODY_RADIUS + size):
                if PRINT:
                    print(f"❌ {self.id}: Organ {organ.size} at {organ.position} overlaps body at {self.body_pos}.")
                return False

            # ✅ 3. Check overlap with other organs
            for j in range(i + 1, len(self.organs)):
                other = self.organs[j]
                ox, oy = other.position
                osize = other.size

                distance = math.hypot(x - ox, y - oy)
                if distance < (size + osize):
                    if PRINT:
                        print(f"❌ {self.id}: Organ {organ.type} overlaps with {other.type} at {other.position}.")
                    return False

        return True
    
    def serialize_organs(self):
        """Serialize body position + organs (relative to COM) for sprite ID hashing."""

        # Round body position slightly for hash stability
        bx = round(self.body_pos[0], 2)
        by = round(self.body_pos[1], 2)

        # Sort and serialize organs
        sorted_organs = sorted(
            [(o.type, round(o.position[0], 2), round(o.position[1], 2), o.size) for o in self.organs if o.isAlive]
        )

        organ_str = "|".join([f"{t},{x},{y},{s}" for t, x, y, s in sorted_organs])

        return f"body,{bx},{by}|{organ_str}"


    def compute_sprite_id(self):
        """Assign or reuse sprite ID based on serialized organ layout, and optionally generate SVG."""
        serialized = self.serialize_organs()

        with sprite_lock:
            for sid, layout in Creature.sprite_map.items():
                if layout == serialized:
                    return sid  # ✅ Reuse existing layout

            sprite_id = Creature.sprite_counter
            Creature.sprite_map[sprite_id] = serialized
            Creature.sprite_counter += 1
        
        if SVG:

            # ✅ Create SVG visualization
            svg = []
            canvas_size = 150
            half = canvas_size // 2

            svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_size}" height="{canvas_size}" viewBox="{-half} {-half} {canvas_size} {canvas_size}">')

            bx, by = self.body_pos if hasattr(self, 'body_pos') else (0, 0)

            # ➤ Draw connection lines first
            for organ in self.organs:
                if getattr(organ, 'isAlive', True):
                    ox, oy = organ.position
                    svg.append(f'<line x1="{bx}" y1="{by}" x2="{ox}" y2="{oy}" stroke="black" stroke-width="1"/>')

            # ➤ Draw body center
            svg.append(f'<circle cx="{bx}" cy="{by}" r="{BODY_RADIUS}" fill="blue" stroke="black" stroke-width="1"/>')

            # ➤ Draw organs
            for organ in self.organs:
                if getattr(organ, 'isAlive', True):
                    ox, oy = organ.position
                    r = organ.size
                    color = {
                        "mouth": "yellow",
                        "eye": "white",
                        "flipper": "orange",
                        "spike": "red"
                    }.get(organ.type, "gray")

                    svg.append(f'<circle cx="{ox}" cy="{oy}" r="{r}" fill="{color}" stroke="black" stroke-width="1"/>')

            svg.append('</svg>')

            os.makedirs("sprites", exist_ok=True)
            with open(f"sprites/sprite_{sprite_id}.svg", "w") as f:
                f.write("\n".join(svg))

        return sprite_id
    
    def calculate_mass(self):
        """Calculate total mass based on body and organs."""
        # Base mass of the creature's main body (π * r² * density)
        body_mass = math.pi * (BODY_RADIUS ** 2)

        # Sum the mass of all organs (π * r² * density)
        organ_mass = sum(math.pi * (organ.size ** 2) for organ in self.organs if organ.isAlive)

        return body_mass + organ_mass
    
    def calculate_com(self):

        weighted_x = -sum(organ.position[0] * (math.pi * organ.size ** 2) for organ in self.organs if organ.isAlive)
        weighted_y = -sum(organ.position[1] * (math.pi * organ.size ** 2) for organ in self.organs if organ.isAlive)

        return [weighted_x / self.mass, weighted_y / self.mass]
    

    
    def calculate_rotational_inertia(self):
        """Compute rotational inertia relative to the center of mass (now at position [0,0])."""

        inertia = 0

        for organ in self.organs:
            if not organ.isAlive: continue
            organ_mass = math.pi * (organ.size ** 2)  # Assume unit density: mass = area
            r = math.hypot(organ.position[0], organ.position[1])  # Already relative to COM
            inertia += organ_mass * (r ** 2)  # I = Σ(m * r²)

        # Optionally include the body's inertia if it's not centered
        body_mass = math.pi * (BODY_RADIUS ** 2)
        r_body = math.hypot(self.body_pos[0], self.body_pos[1])
        inertia += body_mass * (r_body ** 2)

        return inertia if inertia > 0 else 1
    
    
    def apply_force(self, angle, magnitude, world_position):
        """Apply force in world space, using center-of-mass as origin."""

        # ✅ Ignore very small forces
        if magnitude < 0.001:
            return

        # ✅ Compute force vector from angle
        force_x = math.cos(angle) * magnitude
        force_y = math.sin(angle) * magnitude

        # ✅ Apply linear acceleration
        self.velocity[0] += force_x / self.mass
        self.velocity[1] += force_y / self.mass

        # ✅ Compute position of application relative to center of mass
        rel_x = world_position[0] - self.position[0]
        rel_y = world_position[1] - self.position[1]

        # ✅ Apply torque if the force is off-center
        torque = (rel_x * force_y) - (rel_y * force_x)

        self.angular_velocity += torque / self.rotational_inertia

        # ✅ Clamp tiny oscillations
        if abs(self.angular_velocity) < 0.0001:
            self.angular_velocity = 0

        # ✅ Debug logging
        if DEBUG:
            if self.id not in Creature.force_log:
                Creature.force_log[self.id] = []

            Creature.force_log[self.id].append({
                "a": angle,
                "m": magnitude,
                "w": world_position
            })


    
    def random_direction(self):
        angle = random.uniform(0, 2 * math.pi)
        return angle

    def move(self):
        speed = 1
        self.position[0] = (self.position[0] + speed) % 500

    def run_organs(self):
        #print(f"🎛️ Running organs for Creature {self.id}")
        for organ in self.organs:
            #print(f"🧩 {organ.type} simulating...")
            organ.simulate()

    def update_position(self):
        """Apply stored velocity & rotation to move creature each frame."""
        import math
        from simulation.simulation.world import world
        frame_count = world.get_frame()

        # ✅ Move using full float precision
        self.position[0] = (self.position[0] + self.velocity[0]) % 500
        self.position[1] = (self.position[1] + self.velocity[1]) % 500

        # ✅ Update direction, normalize, and clamp angle
        self.direction = (self.direction + self.angular_velocity) % (2 * math.pi)


        # ✅ Log movement only distance from last sent position over threshold
        if self.cell:
            dx = abs(self.position[0] - self.last_sent_x)
            dy = abs(self.position[1] - self.last_sent_y)
            dtheta = abs(self.direction - self.last_sent_direction)

            # Wrap direction diff to [0, π] if needed
            if dtheta > math.pi:
                dtheta = 2 * math.pi - dtheta

            parts = []
            if dx > 0.5:
                parts.append(f"x{round(self.position[0], 1)}")
                self.last_sent_x = self.position[0]
            if dy > 0.5:
                parts.append(f"y{round(self.position[1], 1)}")
                self.last_sent_y = self.position[1]
            if dtheta > 0.01:
                parts.append(f"d{round(self.direction, 2)}")
                self.last_sent_direction = self.direction

            if parts:
                move_str = f"m[{self.id}," + ",".join(parts) + "],"
                delta = self.cell.get_current_delta()
                with self.cell.lock:
                    delta["creatures"] += move_str
                    

                # ✅ Apply friction periodically
                if frame_count % FRICTION_STEP == 0:
                    self.velocity[0] *= FRICTION
                    self.velocity[1] *= FRICTION
                    self.angular_velocity *= ANGULAR_FRICTION

            # ✅ Kill if spinning too fast
            if abs(self.angular_velocity) > MAX_AV:
                self.die()

        # ✅ Energy drain
        self.energy -= BMR
        if self.energy <= 0:
            self.die()

        # ✅ Optionally: Snap to integer *after* logic for visuals only
        #self.position[0] = round(self.position[0])
        #self.position[1] = round(self.position[1])



    def reproduce(self):
        """Creates a new creature by cloning, with passive mutations (e.g., organs mutate on copy)."""


        if self.energy < 100:
            return None
    
        self.change_energy(-60)

        #offspring_organs = [organ.copy_mutate() for organ in self.organs]  # Passive mutation happens here

        offspring = Creature(
            position=self.position.copy(),
            mutation_rate=self.mutation_rate,
            user_created=False,
            organs=[organ.copy() for organ in self.organs if organ.isAlive]
        )

        for organ in offspring.organs:
            organ.set_parent(offspring)

        # Spawn nearby
        angle = random.uniform(0, 2 * math.pi)
        offset_x = math.cos(angle) * 100
        offset_y = math.sin(angle) * 100

        offspring.position[0] = (self.position[0] + offset_x) % 500
        offspring.position[1] = (self.position[1] + offset_y) % 500

        # Inherit traits
        offspring.generation = self.generation + 1
        offspring.parent_ids.append(self.id)
        offspring.energy = 50
        offspring.direction = self.random_direction()

        offspring.name = f"{self.name}.{self.offspringcounter:02}"
        self.offspringcounter += 1

        offspring.isAlive = True

        offspring.mutate()

        return offspring
    


    def die(self):
        """Handle creature death by spawning food proportionate to its energy."""
        if PRINT:
            print(f"💀 Creature {self.id} has died.")

        num_food = int(math.floor(self.energy / 25))  # How much food to spawn

        if self.cell:
                
            for _ in range(num_food):
                offset_x = random.randint(-10, 10)
                offset_y = random.randint(-10, 10)

                food_x = min(max(self.position[0] + offset_x, 0), 499)
                food_y = min(max(self.position[1] + offset_y, 0), 499)

                from simulation.simulation.food import Food  # safe here to avoid circular imports
                food = Food([int(food_x), int(food_y)])
                self.cell.add(food)  # ✅ uses delta-logging add()

            self.cell.remove(self)  # ✅ remove self with delta logging

        self.cell = None
        self.isAlive = False

    def mutate(self):
        """Applies mutations based on mutation rate."""

        num_mutations = max(0, int(self.mutation_rate + random.choice([-1, 0, 1])))

        mutation_options = ["organs", "mutation_rate"]

        for _ in range(num_mutations):
            mutation_type = random.choice(mutation_options)

            if mutation_type == "mutation_rate":
                self.mutation_rate = random.randint(1, self.mutation_rate + random.randint(-1, 1))

            elif mutation_type == "organs":
                self.mutate_organs()  # Actually modify organs

        if not self.validate_organs():
            
            self.die()
            return

        # ✅ Recompute sprite_id because organs may have changed
        self.sprite_id = self.compute_sprite_id()

        # Recompute physics variables
        self.mass = self.calculate_mass()

        self.com = self.calculate_com()

        self.rotational_inertia = self.calculate_rotational_inertia()

    def change_energy(self, amount):
        self.energy += amount
        if self.cell:
            delta = self.cell.get_current_delta()
            
            delta["creatures"] += (f"e[{self.id},{self.energy}]")

    def mutate_organs(self):
        """Randomly add, delete, or modify an organ."""
        actions = []

        if len(self.organs) < self.MAX_ORGANS:
            actions.append("add")
        if self.organs:
            actions.extend(["delete", "modify"])

        if not actions:
            return  # No valid actions

        action = random.choice(actions)

        if action == "add":
            organ_type = random.choice(self.ORGANS)
            position = [random.randint(-30, 30), random.randint(-30, 30)]  # Pixel coordinates
            size = random.randint(5, 15)  # Sizes in pixels

            new_organ = Organ.create_organ(organ_type, position, size, parent=self)
            self.organs.append(new_organ)
            if PRINT: print(f"🧬 {self.id}: Added organ {organ_type} at {position} size {size}")

        elif action == "delete":
            removed_organ = self.organs.pop(random.randint(0, len(self.organs) - 1))
            if PRINT: print(f"🗑️ {self.id}: Removed organ {removed_organ.type} at {removed_organ.position}")

        elif action == "modify":
            organ = random.choice(self.organs)
            old_position = organ.position[:]
            old_size = organ.size

            # Mutate position slightly (±5 pixels)
            organ.position[0] += random.randint(-5, 5)
            organ.position[1] += random.randint(-5, 5)

            # Mutate size slightly (±3 pixels), but not smaller than 1
            organ.size = max(1, organ.size + random.randint(-3, 3))

            if PRINT: print(f"🔧 {self.id}: Modified organ {organ.type} from position {old_position}, size {old_size} "
                f"to position {organ.position}, size {organ.size}")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "position": self.position, "direction": self.direction, "sprite_id": self.sprite_id, "energy": self.energy, "isAlive": self.isAlive}

