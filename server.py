from flask import Flask, jsonify, request
import threading
import time
import uuid
import random
import math
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR) 

app = Flask(__name__)

# ----- Constants -----
ENERGY_DECAY = -0.001  # Energy lost per cycle
SIMULATION_SPEED = 0.033  # Time between simulation steps
BASE_REPRODUCTION_CHANCE = 0.05  # Base chance to reproduce
REPRODUCE = True

# ----- Global Simulation State -----
creatures = []
creatures_lock = threading.Lock()

# ----- Organ Base Class -----
class Organ:
    allowed_types = ["mouth", "eye", "flipper", "spike"]  # Static list of all allowed organ types

    def __init__(self, position, size, parent=None):
        self.position = position  # [x, y] relative to center
        self.size = size  # Radius / size in pixels
        self.type = "generic"  # Overridden by subclasses
        self.parent = parent  # Reference to parent Creature

    def set_parent(self, creature):

        self.parent = creature

    def simulate(self):
        """Simulate behavior per frame. Override in child classes if needed."""
        pass



    def mutate(self):
        """Mutate organ's position and size slightly."""
        # Mutate position slightly (±5 pixels)
        self.position[0] += random.randint(-5, 5)
        self.position[1] += random.randint(-5, 5)

        # Mutate size slightly (±3 pixels), but not smaller than 1
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

    def to_dict(self):
        """Serialize for frontend/communication."""
        return {
            "type": self.type,
            "position": self.position,
            "size": self.size
        }
    
    def get_absolute_position(self):
        """Calculate absolute position using parent's position and direction."""
        if not self.parent:
            raise ValueError("Organ has no parent creature assigned!")

        ox, oy = self.position
        dir_x, dir_y = self.parent.direction
        # Rotate position
        rotated_x = ox * dir_x - oy * dir_y
        rotated_y = ox * dir_y + oy * dir_x
        # Add creature's world position
        abs_x = self.parent.position[0] + rotated_x
        abs_y = self.parent.position[1] + rotated_y
        return [abs_x, abs_y]
    
    def copy(self):
        """Return a copy of this organ without a parent (parent set later)."""
        return self.__class__(self.position[:], self.size)  # Make sure position is copied (new list)


# ----- Specific Organ Types -----
class Mouth(Organ):
    def __init__(self, position, size, parent=None):
        super().__init__(position, size, parent)
        self.type = "mouth"

    def simulate(self):

        """Try to eat any nearby food based on organ's position."""
        # ✅ Get mouth's absolute position in world space
        mouth_pos = self.get_absolute_position()

        # ✅ Check for food nearby and eat if in range
        with food_lock:  # Thread-safe food access
            for food_obj in food[:]:  # Safe copy of the list for iteration
                food_pos = food_obj.position
                distance = math.hypot(mouth_pos[0] - food_pos[0], mouth_pos[1] - food_pos[1])

                if distance <= self.size:
                    # ✅ Eat the food, add energy to creature
                    self.parent.energy += 20  # You can adjust energy gain as needed
                    food.remove(food_obj)  # Remove the food from the global list
                    print(f"🍽️ Creature {self.parent.id} ate food at {food_pos} (Energy: {self.parent.energy})")
                    break  # Only eat one food per simulation frame


class Eye(Organ):
    def __init__(self, position, size, parent=None):
        super().__init__(position, size, parent)
        self.type = "eye"

    def simulate(self):
        """Placeholder for vision/sensing functionality."""
        pass


class Flipper(Organ):
    def __init__(self, position, size, parent=None):
        super().__init__(position, size, parent)
        self.type = "flipper"

    def simulate(self):
        """Basic energy cost for having a flipper."""
        self.parent.energy -= 0.05  # Example passive drain


class Spike(Organ):
    def __init__(self, position, size, parent=None):
        super().__init__(position, size, parent)
        self.type = "spike"

    def simulate(self):
        """Placeholder for attack/defense functionality."""
        pass

class Creature:

    ORGANS = ["mouth", "eye", "flipper", "spike"]
    MAX_ORGANS = 5  # Limit on organs per creature
    CENTER_RADIUS = 16  # Fixed radius of central node
    counter = 0  # Static counter for unique IDs

    sprite_map = {}  # {sprite_id: serialized_organs}
    sprite_counter = 0  # For assigning unique sprite IDs

    def __init__(self, position, mutation_rate=1.0, user_created=True, name=None, organs=None):
        # ---- Basic fields ----
        self.id = Creature.counter
        Creature.counter += 1
        self.name = name if name else f"Creature_{self.id}"  # Display name
        self.position = position  # [x, y]
        self.energy = 100  # Default energy
        self.age = 0
        self.mutation_rate = mutation_rate
        self.user_created = user_created
        self.parent_ids = []  # Lineage tracking
        self.generation = 0
        self.direction = self.random_direction()  # Random initial direction
        self.isAlive = True  # Alive flag

        self.organs = []  # Organs will be added below

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
                    print(f"❌ Unknown organ format: {organ_data}")
                    continue  # Skip invalid

                self.organs.append(organ)

        # ✅ Validate organs once all are added
        if not self.validate_organs():
            print(f"❌ Creature {self.id}: Invalid organ layout on creation. Dying.")
            self.die()  # Handle death (e.g., turn to food)
            return  # Stop further processing if invalid

        # ✅ Sprite ID assignment (after validation)
        self.sprite_id = self.compute_sprite_id()

        print(f"✅ Creature {self.id} created with {len(self.organs)} organs. Sprite ID: {self.sprite_id}")

        
        self.sprite_id = self.compute_sprite_id()

        self.isAlive = True

        if not user_created:
            self.mutate()  # Mutate if evolved

    def add_organ(self, organ_type, position, size):
        """Add a new organ, then validate entire layout. Die if invalid."""
        if len(self.organs) >= self.MAX_ORGANS:
            print(f"⚠️ {self.id}: Max organs reached, cannot add more.")
            return False

        size = int(size)
        position = [int(position[0]), int(position[1])]

        new_organ = {
            "type": organ_type,
            "position": position,
            "size": size
        }

        self.organs.append(new_organ)  # Tentatively add

        # ✅ Validate full layout now
        if not self.validate_organs():
            print(f"❌ {self.id}: Adding organ {new_organ} caused invalid layout. Creature will die.")
            self.invalid = True
            self.die()  # Die if overall invalid
            return False  # Indicate organ couldn't be added successfully (because creature died)

        print(f"🧬 {self.id}: Successfully added organ {new_organ}")
        return True  # Organ added and layout valid

    def validate_organs(self):
        """Check if organs overlap each other, the center, or go outside design bounds. Return True if valid, False if not."""
        for i, organ in enumerate(self.organs):
            x, y = organ.position
            size = organ.size

            # ✅ Check if organ goes outside creature's design box (-50 to 50)
            if not (-50 + size <= x <= 50 - size) or not (-50 + size <= y <= 50 - size):
                print(f"❌ {self.id}: Organ {organ.type} at {organ.position} goes out of bounds.")
                return False  # Out of bounds

            # ✅ Check overlap with center
            distance_to_center = math.hypot(x, y)
            if distance_to_center < (self.CENTER_RADIUS + size):
                print(f"❌ {self.id}: Organ {organ.type} at {organ.position} overlaps center.")
                return False  # Overlaps center

            # ✅ Check overlap with other organs
            for j in range(i + 1, len(self.organs)):
                other = self.organs[j]
                ox, oy = other.position
                osize = other.size

                distance = math.hypot(x - ox, y - oy)
                if distance < (size + osize):
                    print(f"❌ {self.id}: Organ {organ.type} overlaps with {other.type}.")
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

    def random_direction(self):
        """Generates a normalized random direction vector [dx, dy]."""
        angle = random.uniform(0, 2 * math.pi)
        return [math.cos(angle), math.sin(angle)]

    def move(self):
        """Move forward in the current direction."""
        speed = 1  # Move one unit per cycle
        self.position[0] = (self.position[0] + self.direction[0] * speed) % 500
        self.position[1] = (self.position[1] + self.direction[1] * speed) % 500

    def rotate(self):
        """Randomly rotate the direction vector by -45 to +45 degrees."""
        theta = random.uniform(-math.pi / 90, math.pi / 90)  # Random angle in radians (-45 to +45 deg)
        cos_t, sin_t = math.cos(theta), math.sin(theta)
        x, y = self.direction
        self.direction = [
            (x * cos_t - y * sin_t),
            (x * sin_t + y * cos_t)
        ]
        # Normalize to keep it a unit vector
        length = math.hypot(*self.direction)
        self.direction = [d / length for d in self.direction]

    def reproduce(self):
        """Creates a new creature with possible mutations."""
        if self.energy < 50:
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

        offspring.generation = self.generation + 1
        offspring.parent_ids.append(self.id)
        offspring.energy = 40
        offspring.direction = self.random_direction()  # New random direction

        offspring.mutate()  # Mutate AFTER organs are set

        return offspring

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
            print(f"🧬 {self.id}: Added organ {organ_type} at {position} size {size}")

        elif action == "delete":
            removed_organ = self.organs.pop(random.randint(0, len(self.organs) - 1))
            print(f"🗑️ {self.id}: Removed organ {removed_organ.type} at {removed_organ.position}")

        elif action == "modify":
            organ = random.choice(self.organs)
            old_position = organ.position[:]
            old_size = organ.size

            # Mutate position slightly (±5 pixels)
            organ.position[0] += random.randint(-5, 5)
            organ.position[1] += random.randint(-5, 5)

            # Mutate size slightly (±3 pixels), but not smaller than 1
            organ.size = max(1, organ.size + random.randint(-3, 3))

            print(f"🔧 {self.id}: Modified organ {organ.type} from position {old_position}, size {old_size} "
                f"to position {organ.position}, size {organ.size}")

    def die(self):
        """Handles creature death: turns into food, marks for removal, logs death."""
        print(f"💀 Creature {self.id} has died.")
        with food_lock:
            food.append(Food(self.position.copy()))  # Turn into food at death position
        self.isAlive = False

    def run_organs(self):
        for organ in self.organs:
            organ.simulate()

    def to_dict(self):
        """Convert to a JSON-friendly dictionary (for state)."""
        return {
            "id": self.id,
            "position": self.position,
            "direction": self.direction,
            "sprite_id": self.sprite_id
        }

# ----- Food Container and Locks -----
food = []  # List to hold food objects
food_lock = threading.Lock()  # Lock for thread-safe access to food
MAX_FOOD = 50  # Maximum amount of food in the world
FOOD_SPAWN_INTERVAL = 3  # Seconds between food spawns

class Food:
    def __init__(self, position):
        self.position = position  # [x, y]

    def to_dict(self):
        return self.position
    
# ----- Food Spawning Loop -----
def food_spawning_loop():
    """Continuously spawns food up to a limit."""
    global food
    while True:
        try:
            with food_lock:
                if len(food) < MAX_FOOD:
                    # Spawn food at a random position
                    new_pos = [random.randint(0, 499), random.randint(0, 499)]
                    
                    # Check if position already used
                    existing_positions = {tuple(f.position) for f in food}  # Store positions as tuples for set comparison

                    if tuple(new_pos) not in existing_positions:
                        new_food = Food(position=new_pos)
                        food.append(new_food)
                        print(f"🍎 Spawned food at {new_food.position} (Total: {len(food)})")

        except Exception as e:
            print(f"⚠️ ERROR in food spawning loop: {e}")

        time.sleep(FOOD_SPAWN_INTERVAL)
    
# ----- Get State Function -----
def get_state():
    """Returns the current state of all creatures and food."""
    with creatures_lock, food_lock:
        creature_data = [c.to_dict() for c in creatures]
        food_data = [f.id_string() for f in food]  # Return as compact id strings
    return {"creatures": creature_data, "food": food_data}
    

# ----- Continuous Simulation Loop -----
def simulation_loop():
    """Continuously runs the simulation in the background."""
    global creatures
    global ENERGY_DECAY
    '''
        if len(creatures) > 10:
            ENERGY_DECAY = 1  # Lose energy if overpopulated
        else:
            ENERGY_DECAY -0.001  # Gain energy if underpopulated
    '''    
    while True:

        with creatures_lock:

            offspring_list = []  # Temporary holder for new creatures

            for creature in creatures:
                creature.age += 1
                if len(creatures) > 20:
                    creature.energy -= 0.01
                else:
                    creature.energy += 0.1
                creature.rotate()
                creature.move()

                creature.run_organs()

                if (REPRODUCE):
                    offspring = creature.reproduce()
                    if offspring:
                        offspring_list.append(offspring)  # ✅ Append to separate list

                if creature.energy <= 0:
                    creature.die()

            # After loop, add all offspring
            creatures.extend(offspring_list)

            # Filter out dead creatures
            creatures = [c for c in creatures if c.isAlive]

        time.sleep(SIMULATION_SPEED)
        '''
        try:
        except Exception as e:
            print(f"⚠️ ERROR in simulation loop: {e}")
        '''


# ----- API Endpoints -----
@app.route('/getstate', methods=['GET'])
def getstate():
    creature_data = [c.to_dict() for c in creatures]
    food_data = [f.to_dict() for f in food]  # Return as compact id strings
    return {"creatures": creature_data, "food": food_data}

@app.route('/getcreatures', methods=['GET'])
def get_creatures():
    """Return organ data and names for creatures."""
    creature_ids = request.args.getlist('id')

    with creatures_lock:
        if creature_ids:
            models = [{'id': c.id, 'name': c.name, 'organs': c.organs} for c in creatures if c.id in creature_ids]
        else:
            models = [{'id': c.id, 'name': c.name, 'organs': c.organs} for c in creatures]

    return jsonify(models)

@app.route('/getsprites', methods=['GET'])
def get_sprites():
    """Return all sprite layouts and their sprite IDs."""
    with creatures_lock:  # Ensure thread-safety
        return jsonify(Creature.sprite_map)


@app.route('/uploadcreature', methods=['POST'])
def upload_creature():
    """Upload a new creature to the simulation."""
    data = request.json
    creature_id = data.get("id", f"user_{uuid.uuid4()}")
    position = data.get("position", [0, 0])
    mutation_rate = float(data.get("mutation_rate", 1.0))
    name = data.get("name", f"Creature_{creature_id}")

    if not isinstance(position, list) or len(position) != 2:
        return jsonify({'status': 'error', 'message': 'Invalid position format.'}), 400

    new_creature = Creature(creature_id, position, mutation_rate, user_created=True, name=name)

    with creatures_lock:
        creatures.append(new_creature)

    return jsonify({'status': 'success', 'message': f'Creature {creature_id} ({name}) added!'})


# ----- Start Server -----
if __name__ == '__main__':
    with creatures_lock:

        creatures.append(Creature(position=[300, 250], organs=[
            {"type": "eye", "position": [25, 0], "size": 5},
            {"type": "mouth", "position": [-25, 0], "size": 5}
        ]))

        creatures.append(Creature(position=[200, 250], organs=[
            {"type": "eye", "position": [30, 0], "size": 6}  # 6 + 10 > 5 distance
        ]))

        creatures.append(Creature(position=[250, 300], organs=[
            {"type": "mouth", "position": [30, 0], "size": 10}  # 6 + 10 > 5 distance
        ]))

        creatures.append(Creature(position=[250, 200], organs=[
            {"type": "flipper", "position": [0, 30], "size": 10},
            {"type": "spike", "position": [30, 30], "size": 10},
            {"type": "spike", "position": [-40, 30], "size": 10}
        ]))
    
    #print (creatures[2].sprite_id)

    print (Creature.sprite_map)

    print("✅ Simulation initialized with starting creatures.")
    sim_thread = threading.Thread(target=simulation_loop, daemon=True)
    sim_thread.start()
    food_thread = threading.Thread(target=food_spawning_loop, daemon=True)
    food_thread.start()
    print("🚀 Simulation running in background. Fetch state via /getstate.")
    app.run(host='127.0.0.1', port=5000, threaded=True)
