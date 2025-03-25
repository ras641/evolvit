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

    def c(pos, organs):  # short helper
        creature = Creature(position=pos, organs=organs)
        cell.add(creature, log_spawn=False)

    c([100, 100], [])
    c([100, 100], [{"type": "flipper", "position": [-30, 0], "size": 5},
                   {"type": "mouth", "position": [25, 0], "size": 5}])
    c([400, 200], [{"type": "flipper", "position": [-30, 0], "size": 5},
                   {"type": "mouth", "position": [25, 0], "size": 5}])
    c([200, 300], [{"type": "flipper", "position": [-30, 0], "size": 5},
                   {"type": "mouth", "position": [25, 0], "size": 5}])
    c([300, 100], [{"type": "mouth", "position": [25, 0], "size": 5}])
    c([100, 300], [{"type": "flipper", "position": [-30, 20], "size": 5},
                   {"type": "mouth", "position": [25, 0], "size": 5}])
    c([100, 250], [{"type": "flipper", "position": [-30, 0], "size": 5},
                   {"type": "mouth", "position": [30, 0], "size": 5}])
    c([200, 250], [{"type": "flipper", "position": [-30, 0], "size": 5},
                   {"type": "mouth", "position": [25, 0], "size": 5}])
    c([300, 250], [{"type": "mouth", "position": [-30, 0], "size": 5},
                   {"type": "mouth", "position": [25, 0], "size": 5}])
    c([400, 250], [{"type": "flipper", "position": [-30, 0], "size": 5},
                   {"type": "mouth", "position": [25, 0], "size": 5}])

def start_simulation():
    print(f"✅ cell_grid initialized with size {len(world.cell_grid)}x{len(world.cell_grid[0])}")
    threading.Thread(target=simulation_loop, daemon=True).start()
    threading.Thread(target=food_spawning_loop, args=(world,), daemon=True).start()
