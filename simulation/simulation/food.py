import random
import time
import threading

import math
import config

food = []
food_lock = threading.Lock()

class Food:
    def __init__(self, position):
        self.position = position

    def to_dict(self):
        return self.position

def food_spawning_loop():

    from simulation.creatures import Creature

    for _ in range(50):
        if len(food) < config.MAX_FOOD:
            new_food = Food(position=[random.randint(0, 499), random.randint(0, 499)])
            food.append(new_food)

    food_spawn_accumulator = 0.0  # Tracks spawn progress over multiple updates
    last_time = time.time()  # Track real-world time


    # Base simulation FPS (acts as a normalizing factor)
    MIN_ELAPSED_TIME = 1 / 1000  # Ensure updates contribute at very high FPS
    MAX_ELAPSED_TIME = 1 / 10    # Prevent extreme lag-induced jumps

    while True:
        num_creatures = Creature.get_creature_count()  # Thread-safe class method

        config.FOOD_SPAWN_INTERVAL = 40 + 0.1 * (num_creatures ** 2)

        time.sleep(config.FOOD_STEP)  # ✅ Prevent excessive CPU usage

        # 🔥 Get real elapsed time but normalize it
        current_time = time.time()
        elapsed_time = current_time - last_time
        last_time = current_time

        # 🔥 Clamp to prevent too small/large updates
        elapsed_time = max(MIN_ELAPSED_TIME, min(elapsed_time, MAX_ELAPSED_TIME))

        # 🔥 Normalize for high-FPS consistency (scaling factor ensures contribution even at high FPS)
        normalized_elapsed = elapsed_time * config.FPS  # This makes behavior FPS-independent
        food_spawn_accumulator += normalized_elapsed / config.FOOD_SPAWN_INTERVAL

        with food_lock:
            spawn_count = int(food_spawn_accumulator)  # Ensure food spawns when accumulation reaches 1.0
            food_spawn_accumulator -= spawn_count  # Retain remainder for next loop

            #print(f"Spawning {spawn_count} food items (Accumulator: {food_spawn_accumulator})")

            for _ in range(spawn_count):
                if len(food) < config.MAX_FOOD:
                    new_food = Food(position=[random.randint(0, 499), random.randint(0, 499)])
                    food.append(new_food)

