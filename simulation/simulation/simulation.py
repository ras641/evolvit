import threading
import time
from simulation.creatures import Creature
from simulation.food import food_spawning_loop

import os
import shutil

import config

from .creatures import *

def simulation_loop():

    global frame_count

    while True:

        Creature.force_log.clear()

        Creature.run_creatures()  # ✅ Run all creature updates inside the class

        time.sleep(SIMULATION_SPEED)

        config.frame_count += 1

        if len(Creature.creatures) == 0 and False:

            initialize_simulation()

def start_simulation():

    # 🧹 Clear all files in the /sprites/ directory
    sprite_dir = "./sprites"
    if os.path.exists(sprite_dir):
        for filename in os.listdir(sprite_dir):
            file_path = os.path.join(sprite_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)  # Delete file or symlink
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)  # Delete folder recursively
            except Exception as e:
                print(f"⚠️ Failed to delete {file_path}: {e}")
    else:
        os.makedirs(sprite_dir)  # Create the folder if it doesn't exist

    initialize_simulation()

    threading.Thread(target=simulation_loop, daemon=True).start()
    threading.Thread(target=food_spawning_loop, daemon=True).start()

def initialize_simulation():
    """Generate some initial creatures for testing."""
    with Creature.creatures_lock:

        Creature.creatures.append(Creature(position=[100, 250], organs=[
            {"type": "flipper", "position": [-30, 0], "size": 5},
            {"type": "spike", "position": [25, 0], "size": 5}
            
        ]))
        

        Creature.creatures.append(Creature(position=[400, 100], organs=[
            {"type": "flipper", "position": [-30, 0], "size": 5},
            {"type": "mouth", "position": [25, 0], "size": 5}
        ]))

        Creature.creatures.append(Creature(position=[200, 250], organs=[
            {"type": "mouth", "position": [-35, 0], "size": 5},
            {"type": "spike", "position": [25, 0], "size": 5}
            
        ]))

        Creature.creatures.append(Creature(position=[300, 250], organs=[
            {"type": "mouth", "position": [30, 0], "size": 5},
            {"type": "spike", "position": [25, 25], "size": 5},
            
            {"type": "flipper", "position": [-30, 30], "size": 5}
            
        ]))
        

    if PRINT: print(f"✅ Initialized {len(Creature.creatures)} creatures.")
