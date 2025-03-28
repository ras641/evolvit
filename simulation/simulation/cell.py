import threading
import random
import math
import simulation.config as config
import json

class Cell:

    BUFFER_FRAMES = 300

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.creatures = []
        self.food = []
        self.lock = threading.RLock()
        #print(f"🧱 Created Cell({x}, {y})")

        self.state_buffer = [{}, {}]
        self.building = 0
        self.snapshot = ""

        self.delta_frames = [None] * Cell.BUFFER_FRAMES


        self.current_delta = {
            i: {
                "frame": i,
                "new_food": "",
                "deleted_food": "",
                "creatures": ""
            } for i in range(Cell.BUFFER_FRAMES)
        }

        self.used_sprite_ids = [set(), set(), set()]
        self.sprite_buffer_index = 0

    def swap_buffers(self, frame):
        """
        Called at the end of a delta block (e.g., at frame X + 300),
        to finalize the current buffer (which has deltas from X+1 to X+300),
        and start building the next one from a new snapshot at X+300.
        """
        import copy

        # Finalize the current build buffer
        self.state_buffer[self.building]["frame"] = frame - Cell.BUFFER_FRAMES  # snapshot corresponds to frame X
        self.state_buffer[self.building]["state"] = self.snapshot
        self.state_buffer[self.building]["deltas"] = copy.deepcopy(self.current_delta)

        # Switch buffers
        self.building = 1 - self.building
        self.sprite_buffer_index = (self.sprite_buffer_index + 1) % 3

        # New snapshot starts at frame X+300
        self.snapshot = {
            "creatures": [c.to_dict() for c in self.creatures],
            "food": [f.to_dict() for f in self.food]
        }

        # Reset deltas for the next block
        for i in range(Cell.BUFFER_FRAMES):
            self.current_delta[i]["new_food"] = ""
            self.current_delta[i]["deleted_food"] = ""
            self.current_delta[i]["creatures"] = ""


        self.used_sprite_ids[self.sprite_buffer_index] = {
            creature.get("sprite_id")
            for creature in self.snapshot.get("creatures", [])
            if creature.get("sprite_id") is not None
        }

        print (self.used_sprite_ids)

    def get_full(self):
        from simulation.simulation.world import world

        state = self.state_buffer[1 - self.building]
        base_frame = world.get_built_index()

        snapshot = {
            "creatures": [
                {
                    **dict(c),
                    "position": [round(c["position"][0]), round(c["position"][1])],
                    "direction": round(c["direction"], 2),
                    "id": c["id"],
                    "name": c["name"]
                }
                for c in state.get("state", {}).get("creatures", [])
            ],
            "food": state.get("state", {}).get("food", [])
        }

        filtered_deltas = {
            str(int(frame) + base_frame): {
                k: v for k, v in delta.items() if k != "frame"
            }
            for frame, delta in state.get("deltas", {}).items()
            if delta.get("creatures") or delta.get("new_food") or delta.get("deleted_food")
        }

        return {
            "frame": state["frame"],
            "state": snapshot,
            "deltas": filtered_deltas
        }
    
    def get_state(self):
        state = self.state_buffer[1 - self.building]

        return {
            "creatures": [
                {
                    **dict(c),
                    "position": [round(c["position"][0]), round(c["position"][1])],
                    "direction": round(c["direction"], 2),
                    "id": c["id"],
                    "name": c["name"]
                }
                for c in state.get("state", {}).get("creatures", [])
            ],
            "food": state.get("state", {}).get("food", [])
        }
    
    def get_live_state(self):
        return {
            "creatures": [
                {
                    "id": c.id,
                    "name": c.name,
                    "position": [round(c.position[0]), round(c.position[1])],
                    "direction": round(c.direction, 2),
                    "energy": c.energy,
                    "sprite_id": c.sprite_id
                }
                for c in self.creatures
                if c.isAlive  # optionally skip dead creatures
            ],
            "food": [
                [round(f.position[0]), round(f.position[1])]
                for f in self.food
            ]
        }
    
    def get_deltas(self):
        from simulation.simulation.world import world

        state = self.state_buffer[1 - self.building]
        base_frame = world.get_built_index()

        filtered_deltas = {
            str(int(frame) + base_frame): {
                k: v for k, v in delta.items() if k != "frame"
            }
            for frame, delta in state.get("deltas", {}).items()
            if delta.get("creatures") or delta.get("new_food") or delta.get("deleted_food")
        }

        return {
            "frame": state["frame"],
            "deltas": filtered_deltas
        }



    
    def get_current_delta(self):
        from simulation.simulation.world import world
        frame_count = world.get_frame()
        index = frame_count % Cell.BUFFER_FRAMES

        # Wipe if this slot is from a past frame
        if self.delta_frames[index] != frame_count:
            self.current_delta[index] = {
                "new_food": "",
                "deleted_food": "",
                "creatures": ""
            }
            self.delta_frames[index] = frame_count

        return self.current_delta[index]



    def add(self, obj, log_spawn=True):
        from .creatures import Creature
        from .food import Food

        with self.lock:
            delta = self.get_current_delta()

            if isinstance(obj, Creature):
                self.creatures.append(obj)
                obj.cell = self

                # 🔼 Track used sprite IDs for this update
                self.used_sprite_ids[self.sprite_buffer_index].add(obj.sprite_id)

                #print ("new")
                if log_spawn:
                    creature_dict = {
                        "id": obj.id,
                        "position": obj.position,
                        "direction": obj.direction,
                        "sprite_id": obj.sprite_id,
                        "name": obj.name,
                        "parent_ids": obj.parent_ids,
                        "creator": obj.creator
                    }
                    delta["creatures"] += f"j{json.dumps(creature_dict)},"
            elif isinstance(obj, Food):

                self.food.append(obj)
                obj.cell = self
                delta["new_food"] += f"[{obj.position[0]},{obj.position[1]}],"




    def remove(self, obj):
        from .creatures import Creature
        from .food import Food

        with self.lock:
            try:
                delta = self.get_current_delta()

                if isinstance(obj, Creature):
                    self.creatures.remove(obj)
                    obj.cell = None
                    delta["creatures"] += f"r[{obj.id}],"

                elif isinstance(obj, Food):
                    self.food.remove(obj)
                    obj.cell = None
                    delta["deleted_food"] += f"[{obj.position[0]},{obj.position[1]}],"
            except ValueError:
                pass  # Already removed




    def add_food(self):
        
        from .food import Food

        self.food.append(Food(position=[random.randint(0, 499), random.randint(0, 499)]))


    def get_used_sprite_ids(self):
        return set().union(*self.used_sprite_ids)

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

            cos_theta_a = math.cos(creature.direction)
            sin_theta_a = math.sin(creature.direction)

            body_rx_a = creature.body_pos[0] * cos_theta_a - creature.body_pos[1] * sin_theta_a
            body_ry_a = creature.body_pos[0] * sin_theta_a + creature.body_pos[1] * cos_theta_a

            body_a = [
                creature.position[0] + body_rx_a,
                creature.position[1] + body_ry_a
            ]

            for j in range(i + 1, len(local_creatures)):
                other = local_creatures[j]


                cos_theta_b = math.cos(other.direction)
                sin_theta_b = math.sin(other.direction)

                body_rx_b = other.body_pos[0] * cos_theta_b - other.body_pos[1] * sin_theta_b
                body_ry_b = other.body_pos[0] * sin_theta_b + other.body_pos[1] * cos_theta_b

                body_b = [
                    other.position[0] + body_rx_b,
                    other.position[1] + body_ry_b
                ]

                # 1️⃣ Body-to-Body Collision
                dx = body_b[0] - body_a[0]
                dy = body_b[1] - body_a[1]
                distance = math.hypot(dx, dy)
                min_distance = config.BODY_RADIUS * 2
                overlap = max(0, min_distance - distance)

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
                    min_distance = config.BODY_RADIUS + organ.size
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
                    min_distance = config.BODY_RADIUS + organ.size
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