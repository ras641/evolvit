# simulation.py
import threading
import time
from .creatures import Creature
from .food import food_spawning_loop
from .world import world

SIMULATION_SPEED = 1 / 30.0  # 30 FPS
PRINT = True

def simulation_loop():
    initialize_creatures(world)
    
    # Setup initial snapshot
    cell = world.cell_grid[0][0]
    cell.snapshot = {
        "creatures": [c.to_dict() for c in cell.creatures],
        "food": [f.to_dict() for f in cell.food]
    }

    while True:

        world.cell_grid[0][0].run_creatures()
        world.cell_grid[0][0].run_collisions()

        world.advance_frame()
        time.sleep(SIMULATION_SPEED)

def initialize_creatures(world):
    cell = world.cell_grid[0][0]

    def c(pos, organs, name):  # short helper
        creature = Creature(position=pos, organs=organs, name=name)
        cell.add(creature, log_spawn=False)

    c([150, 250], [
        {"type": "mouth", "position": [-30, -30], "size": 10},
        {"type": "flipper", "position": [-30, 30], "size": 5},
        {"type": "eye", "position": [30, -30], "size": 10},
        {"type": "spike", "position": [30, 30], "size": 10}
        ]
    , "Xman")

def start_simulation():
    print(f"✅ cell_grid initialized with size {len(world.cell_grid)}x{len(world.cell_grid[0])}")
    threading.Thread(target=simulation_loop, daemon=True).start()
    threading.Thread(target=food_spawning_loop, args=(world,), daemon=True).start()
