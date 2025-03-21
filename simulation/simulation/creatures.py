import random
import math
from simulation.organs import Organ
from simulation.food import food, food_lock, Food
import threading

from config import *

class Creature:

    ORGANS = ["mouth", "eye", "flipper", "spike"]
    MAX_ORGANS = 5
    counter = 0

    sprite_map = {}  # {sprite_id: serialized_organs}
    sprite_counter = 0  # For assigning unique sprite IDs

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

        BASE_REPULSION_FORCE = 20  # ✅ Minimum push force
        MAX_REPULSION_FORCE = 60   # ✅ Cap on maximum push force

        for i, creature in enumerate(Creature.creatures):
            for j in range(i + 1, len(Creature.creatures)):
                other = Creature.creatures[j]

                # ✅ 1️⃣ Check Central Body-to-Body Collisions
                dx = other.position[0] - creature.position[0]
                dy = other.position[1] - creature.position[1]
                distance = math.hypot(dx, dy)
                min_distance = BODY_RADIUS * 2  # ✅ Using dynamic BODY_RADIUS
                overlap = max(0, min_distance * 1.05 - distance)  # ✅ Slightly increase threshold to avoid precision issues

                if overlap > 0:
                    contact_point = [
                        (creature.position[0] + other.position[0]) / 2,
                        (creature.position[1] + other.position[1]) / 2
                    ]

                    # ✅ Scale repulsion force based on overlap depth (capped)
                    repulsion_force = min(BASE_REPULSION_FORCE + overlap * 2, MAX_REPULSION_FORCE)
                    force_direction = math.atan2(dy, dx)
                    creature.apply_force(force_direction + math.pi, repulsion_force, contact_point)
                    other.apply_force(force_direction, repulsion_force, contact_point)

                    # ✅ Apply momentum transfer only if enabled
                    if apply_momentum:
                        Creature.resolve_momentum_transfer(creature, None, other, None, contact_point)

                # ✅ 2️⃣ Check Organ-to-Organ Collisions
                for organ_a in creature.organs:
                    for organ_b in other.organs:
                        pos_a = organ_a.get_absolute_position()
                        pos_b = organ_b.get_absolute_position()

                        dx = pos_b[0] - pos_a[0]
                        dy = pos_b[1] - pos_a[1]
                        distance = math.hypot(dx, dy)
                        min_distance = organ_a.size + organ_b.size
                        overlap = max(0, min_distance - distance)  # ✅ Compute overlap depth

                        if overlap > 0:
                            contact_point = [(pos_a[0] + pos_b[0]) / 2, (pos_a[1] + pos_b[1]) / 2]

                            # ✅ Scale repulsion force based on overlap (capped)
                            repulsion_force = min(BASE_REPULSION_FORCE + overlap * 2, MAX_REPULSION_FORCE)
                            force_direction = math.atan2(dy, dx)
                            creature.apply_force(force_direction + math.pi, repulsion_force, contact_point)
                            other.apply_force(force_direction, repulsion_force, contact_point)

                            # ✅ Apply momentum transfer only if enabled
                            if apply_momentum:
                                Creature.resolve_momentum_transfer(creature, organ_a, other, organ_b, contact_point)


                # 3 Check creature.body-to-other.organ Collisions
                for organ in other.organs:
                    pos_organ = organ.get_absolute_position()

                    # Other's body collides with creature’s organ
                    dx = creature.position[0] - pos_organ[0]
                    dy = creature.position[1] - pos_organ[1]
                    distance = math.hypot(dx, dy)
                    min_distance = BODY_RADIUS + organ.size * 1.1
                    overlap = max(0, min_distance - distance)

                    if overlap > 0:
                        contact_point = [(creature.position[0] + pos_organ[0]) / 2, (creature.position[1] + pos_organ[1]) / 2]
                        repulsion_force = min(BASE_REPULSION_FORCE + overlap * 2, MAX_REPULSION_FORCE)
                        force_direction = math.atan2(dy, dx)

                        other.apply_force(force_direction + math.pi, repulsion_force, contact_point)
                        creature.apply_force(force_direction, repulsion_force, contact_point)  # If organs have physics



                # 4 Check other.body-to-creature.organ Collisions
                for organ in creature.organs:
                    pos_organ = organ.get_absolute_position()

                    # Creature body collides with other’s organ
                    dx = other.position[0] - pos_organ[0]
                    dy = other.position[1] - pos_organ[1]
                    distance = math.hypot(dx, dy)
                    min_distance = BODY_RADIUS + organ.size * 1.1  # ✅ Using dynamic BODY_RADIUS
                    overlap = max(0, min_distance - distance)

                    if overlap > 0:
                        contact_point = [(other.position[0] + pos_organ[0]) / 2, (other.position[1] + pos_organ[1]) / 2]
                        repulsion_force = min(BASE_REPULSION_FORCE + overlap * 2, MAX_REPULSION_FORCE)
                        force_direction = math.atan2(dy, dx)

                        creature.apply_force(force_direction + math.pi, repulsion_force, contact_point)
                        other.apply_force(force_direction, repulsion_force, contact_point)  # If organs have physics








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
        self.position = position
        self.energy = 50
        self.age = 0
        self.mutation_rate = mutation_rate
        self.user_created = user_created
        self.parent_ids = []
        self.generation = 0
        self.direction = 0
        self.isAlive = True
        self.organs = []

        self.velocity = [0,0]
        self.angular_velocity = 0

        # ✅ Compute mass first to avoid undefined attribute issues
        self.mass = 1  # Default to prevent division errors
        self.com = [0, 0]  # Default center of mass
        self.rotational_inertia = 1  # Prevent division by zero
        # ---- Organ setup ----
        if organs:
            for organ_data in organs:
                if isinstance(organ_data, Organ):
                    # If it's already an Organ object (e.g., from copy)
                    organ = organ_data
                    organ.set_parent(self)  # Set parent properly
                elif isinstance(organ_data, dict):
                    # If it's a dict (e.g., from upload)
                    organ_type = organ_data["type"]
                    position = organ_data["position"]
                    size = organ_data["size"]
                    organ = Organ.create_organ(organ_type, position, size, parent=self)
                else:
                    if PRINT: print(f"❌ Unknown organ format: {organ_data}")
                    continue  # Skip invalid

                self.organs.append(organ)

        if not self.validate_organs():

            self.die()

            return
                # ✅ Sprite ID assignment (after validation)

        self.mass = self.calculate_mass()

        self.com = self.calculate_com()

        self.rotational_inertia = self.calculate_rotational_inertia()

        self.sprite_id = self.compute_sprite_id()

        if PRINT: print(f"✅ Creature {self.id} created with {len(self.organs)} organs. Sprite ID: {self.sprite_id}")

        self.isAlive = True

    def validate_organs(self):
        """Check if organs overlap each other, the center, or go outside design bounds. Return True if valid, False if not."""
        for i, organ in enumerate(self.organs):
            x, y = organ.position
            size = organ.size

            # ✅ Check if organ goes outside creature's design box (-50 to 50)
            if not (-50 + size <= x <= 50 - size) or not (-50 + size <= y <= 50 - size):
                if PRINT: print(f"❌ {self.id}: Organ {organ.type} at {organ.position} goes out of bounds.")
                return False  # Out of bounds

            # ✅ Check overlap with center
            distance_to_center = math.hypot(x, y)
            if distance_to_center < (BODY_RADIUS + size):
                if PRINT: print(f"❌ {self.id}: Organ {organ.type} at {organ.position} overlaps center.")
                return False  # Overlaps center

            # ✅ Check overlap with other organs
            for j in range(i + 1, len(self.organs)):
                other = self.organs[j]
                ox, oy = other.position
                osize = other.size

                distance = math.hypot(x - ox, y - oy)
                if distance < (size + osize):
                    if PRINT: print(f"❌ {self.id}: Organ {organ.type} overlaps with {other.type}.")
                    return False  # Overlaps another organ

        return True  # ✅ All checks passed
    
    def serialize_organs(self):
        """Serialize organs into a string for hashing/comparison."""
        sorted_organs = sorted(
            [(o.type, o.position[0], o.position[1], o.size) for o in self.organs]
        )
        return "|".join([f"{t},{x},{y},{s}" for t, x, y, s in sorted_organs])

    def compute_sprite_id(self):
        """Assign or reuse sprite ID based on serialized organ layout."""
        serialized = self.serialize_organs()
        # Check if layout already exists
        for sid, layout in Creature.sprite_map.items():
            if layout == serialized:
                return sid  # Reuse existing sprite ID
        # If not found, create new sprite ID
        sprite_id = Creature.sprite_counter
        Creature.sprite_map[sprite_id] = serialized
        Creature.sprite_counter += 1
        return sprite_id
    
    def calculate_mass(self):
        """Calculate total mass based on body and organs."""
        # Base mass of the creature's main body (π * r² * density)
        body_mass = math.pi * (BODY_RADIUS ** 2)

        # Sum the mass of all organs (π * r² * density)
        organ_mass = sum(math.pi * (organ.size ** 2) for organ in self.organs)

        return body_mass + organ_mass
    
    def calculate_com(self):

        weighted_x = sum(organ.position[0] * (math.pi * organ.size ** 2) for organ in self.organs)
        weighted_y = sum(organ.position[1] * (math.pi * organ.size ** 2) for organ in self.organs)

        return [weighted_x / self.mass, weighted_y / self.mass]
    

    
    def calculate_rotational_inertia(self):

        inertia = 0
        for organ in self.organs:
            # ✅ Distance from COM, not just (0,0)
            r = math.hypot(
                organ.position[0] - self.com[0], 
                organ.position[1] - self.com[1]
            )
            organ_mass = math.pi * (organ.size ** 2)  # Mass = πr² (density = 1)
            inertia += organ_mass * (r ** 2)  # Rotational inertia = Σ (m * r²)

        return inertia if inertia > 0 else 1  # Prevent divide-by-zero
    
    def get_absolute_com(self):
        """Calculate absolute Center of Mass (COM) in world space."""
        com_x, com_y = self.com  # Relative COM stored in creature

        # ✅ Convert parent's direction (radians) into cosine & sine values
        cos_theta = math.cos(self.direction)
        sin_theta = math.sin(self.direction)

        # ✅ Rotate COM relative to creature's direction
        rotated_x = com_x * cos_theta - com_y * sin_theta
        rotated_y = com_x * sin_theta + com_y * cos_theta

        # ✅ Compute absolute COM position
        abs_com_x = self.position[0] + rotated_x
        abs_com_y = self.position[1] + rotated_y
        return [abs_com_x, abs_com_y]
    
    def apply_force(self, angle, magnitude, world_position):
        """Apply force in world space, optimizing torque calculations and logging force applications for debugging."""

        # ✅ Ignore very small forces to reduce unnecessary calculations
        if magnitude < 0.01:
            return  # Skip applying force if it's too small to matter

        # ✅ Precompute force vector once
        force_x = math.cos(angle) * magnitude
        force_y = math.sin(angle) * magnitude

        # ✅ Apply acceleration
        self.velocity[0] += force_x / self.mass
        self.velocity[1] += force_y / self.mass

        # ✅ Compute relative position from Center of Mass (COM)
        absolute_com = self.get_absolute_com()
        rel_x = world_position[0] - absolute_com[0]
        rel_y = world_position[1] - absolute_com[1]

        # ✅ Skip torque calculation if force is near COM OR force is too weak
        if abs(rel_x) > 0.01 or abs(rel_y) > 0.01:
            torque = (rel_x * force_y) - (rel_y * force_x)

            # ✅ Ignore insignificant torque to prevent micro-oscillations
            if abs(torque) > 0.001:
                self.angular_velocity += (torque / self.rotational_inertia)

                # ✅ Apply a dead zone to stop tiny oscillations
                if abs(self.angular_velocity) < 0.0001:
                    self.angular_velocity = 0

        if (DEBUG):

            # ✅ Log the force application in the static dictionary
            if self.id not in Creature.force_log:
                Creature.force_log[self.id] = []  # Initialize list if first time logging this creature

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
        for organ in self.organs:
            organ.simulate()

    def update_position(self):
        """Apply stored velocity & rotation to move creature each frame."""
        
        # ✅ Update position with velocity and wrap around the 500x500 world
        self.position[0] = (self.position[0] + self.velocity[0]) % 500
        self.position[1] = (self.position[1] + self.velocity[1]) % 500



        # ✅ Step 2: Get the absolute world position of the center of mass
        absolute_com = self.get_absolute_com()

        # ✅ Step 3: Update direction based on angular velocity
        self.direction = (self.direction + self.angular_velocity) % (2 * math.pi)  # Keep in range [0, 2π]

        # ✅ Step 4: Adjust position based on rotation around absolute_com
        # Compute current offset of `position` from the absolute center of mass
        offset_x = self.position[0] - absolute_com[0]
        offset_y = self.position[1] - absolute_com[1]

        # Apply small-angle rotation transformation
        cos_theta = math.cos(self.angular_velocity)
        sin_theta = math.sin(self.angular_velocity)

        rotated_x = offset_x * cos_theta - offset_y * sin_theta
        rotated_y = offset_x * sin_theta + offset_y * cos_theta

        # Compute new position based on rotated offset
        self.position[0] = absolute_com[0] + rotated_x
        self.position[1] = absolute_com[1] + rotated_y






        if frame_count % FRICTION_STEP == 0:

            self.velocity[0] *= FRICTION
            self.velocity[1] *= FRICTION
            self.angular_velocity *= (FRICTION ** 2) # Slowly decay rotation

            # ✅ Kill the creature if rotation exceeds a hard limit
            if abs(self.angular_velocity) > MAX_AV:
                self.die()  # Make sure this method is properly defined

        self.energy -= BMR

    def reproduce(self):
        """Creates a new creature with possible mutations."""
        if self.energy < 70:
            return None  # No reproduction this cycle

        self.energy -= 50

        offspring = Creature(
            position=self.position.copy(),  # Copy position
            mutation_rate=self.mutation_rate,
            user_created=False,
            organs=[organ.copy() for organ in self.organs]  # Create fresh copies of organs
        )

        # Set parent creature for each copied organ
        for organ in offspring.organs:
            organ.set_parent(offspring)

        angle = random.uniform(0, 2 * math.pi)  # Random direction in radians
        offset_x = math.cos(angle) * 50
        offset_y = math.sin(angle) * 50

        offspring.position[0] = (self.position[0] + offset_x) % 500
        offspring.position[1] = (self.position[1] + offset_y) % 500

        offspring.generation = self.generation + 1
        offspring.parent_ids.append(self.id)
        offspring.energy = 40
        offspring.direction = self.random_direction()  # New random direction

        # ✅ Recalculate physics properties (Fix missing `mass` issue)
        offspring.mass = offspring.calculate_mass()
        offspring.com = offspring.calculate_com()
        offspring.rotational_inertia = offspring.calculate_rotational_inertia()

        offspring.mutate()  # Mutate AFTER organs are set

        return offspring

    def die(self):
        """Handle creature death by spawning food proportionate to its energy."""
        if PRINT: print(f"💀 Creature {self.id} has died.")

        num_food = 1 + math.floor(self.energy / 20)  # Calculate number of food items to drop

        with food_lock:  # Ensure thread safety
            for _ in range(num_food):
                # Generate a random offset (within ±10 pixels) so food isn't stacked
                offset_x = random.randint(-10, 10)
                offset_y = random.randint(-10, 10)

                # Ensure the food spawns within the world bounds (500x500)
                food_x = min(max(self.position[0] + offset_x, 0), 499)
                food_y = min(max(self.position[1] + offset_y, 0), 499)

                # Spawn new food at the calculated position
                food.append(Food([food_x, food_y]))

        self.isAlive = False  # Mark creature as dead

    def mutate(self):
        """Applies mutations based on mutation rate."""

        num_mutations = max(1, int(self.mutation_rate + random.choice([-1, 0, 1])))

        num_mutations = random.randint(0,5)

        mutation_options = ["organs", "mutation_rate"]

        for _ in range(num_mutations):
            mutation_type = random.choice(mutation_options)

            if mutation_type == "mutation_rate":
                self.mutation_rate = max(0, self.mutation_rate + random.randint(-1, 1))

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
        return {"id": self.id, "position": self.position, "direction": self.direction, "sprite_id": self.sprite_id}

