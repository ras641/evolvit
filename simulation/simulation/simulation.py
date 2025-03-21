import threading
import time
from simulation.creatures import Creature
from simulation.food import food_spawning_loop

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

    initialize_simulation()

    threading.Thread(target=simulation_loop, daemon=True).start()
    threading.Thread(target=food_spawning_loop, daemon=True).start()

def initialize_simulation():
    """Generate some initial creatures for testing."""
    with Creature.creatures_lock:

        Creature.creatures.append(Creature(position=[100, 250], organs=[

            {"type": "flipper", "position": [0, 40], "size": 10}
        ]))
        
        
        Creature.creatures.append(Creature(position=[200, 250], organs=[
            {"type": "mouth", "position": [30, 0], "size": 10},
            {"type": "flipper", "position": [-25, 0], "size": 5}
        ]))

        Creature.creatures.append(Creature(position=[300, 250], organs=[

            {"type": "mouth", "position": [-30, 0], "size": 10},
        ]))

        Creature.creatures.append(Creature(position=[400, 250], organs=[

            {"type": "flipper", "position": [0, -40], "size": 10}
        ]))

        Creature.creatures.append(Creature(position=[200, 200], organs=[
            {"type": "mouth", "position": [30, 5], "size": 10},
            {"type": "flipper", "position": [-25, -5], "size": 5}
        ]))
        

    if PRINT: print(f"✅ Initialized {len(Creature.creatures)} creatures.")
