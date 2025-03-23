import threading
import time
from .creatures import Creature
from .world import creatures, creatures_lock, cell_grid
from .food import food_spawning_loop

#from .creatures import Creature

from .cell import Cell

import os
import shutil

import simulation.config as config

GRID_WIDTH = 10
GRID_HEIGHT = 10

# Create 2D array (grid[y][x])
#cell_grid = [[Cell(x, y) for x in range(GRID_WIDTH)] for y in range(GRID_HEIGHT)]

def simulation_loop():

    import simulation.simulation.world as world

    while True:

        world.cell_grid[0][0].run_creatures()
        world.cell_grid[0][0].run_collisions()

        time.sleep(config.SIMULATION_SPEED)

        config.frame_count += 1

def initialize_cell_grid():
    print("📦 Inside initialize_cell_grid()")
    grid = []
    for x in range(10):
        row = []
        for y in range(10):
            row.append(Cell(x, y))
        grid.append(row)

    grid[0][0].add(Creature(position=[100, 100], organs=[
    ]))

    

    grid[0][0].add(Creature(position=[100, 100], organs=[
            {"type": "flipper", "position": [-30, 0], "size": 5},
            {"type": "mouth", "position": [25, 0], "size": 5}
        ]))
    
    grid[0][0].add(Creature(position=[400, 200], organs=[
        {"type": "flipper", "position": [-30, 0], "size": 5},
        {"type": "mouth", "position": [25, 0], "size": 5}
    ]))

    grid[0][0].add(Creature(position=[200, 300], organs=[
        {"type": "flipper", "position": [-30, 0], "size": 5},
        {"type": "mouth", "position": [25, 0], "size": 5}
    ]))

    grid[0][0].add(Creature(position=[300, 100], organs=[
        {"type": "mouth", "position": [25, 0], "size": 5}
    ]))
    
    grid[0][0].add(Creature(position=[100, 300], organs=[
        {"type": "flipper", "position": [-30, 5], "size": 5},
        {"type": "mouth", "position": [25, 0], "size": 5}
    ]))

    grid[0][0].add(Creature(position=[100, 250], organs=[
        {"type": "flipper", "position": [-30, 0], "size": 5}
    ]))

    grid[0][0].add(Creature(position=[200, 250], organs=[
        {"type": "mouth", "position": [25, 0], "size": 5}
    ]))
    
    grid[0][0].add(Creature(position=[300, 250], organs=[
        {"type": "mouth", "position": [-30, 0], "size": 5},
        {"type": "mouth", "position": [25, 0], "size": 5}
    ]))

    grid[0][0].add(Creature(position=[400, 250], organs=[
    ]))
    
    

    import simulation.simulation.world as world
    world.cell_grid = grid

    print("✅ cell_grid assignment done.")

def start_simulation():

    import simulation.simulation.world as world

    initialize_cell_grid()

    if world.cell_grid is None:
        print("❌ cell_grid is still None!")
    else:
        print(f"✅ cell_grid initialized with size {len(world.cell_grid)}x{len(world.cell_grid[0])}")

    #world.cell_grid[0][0].print_info()

    time.sleep(1)
    threading.Thread(target=simulation_loop, daemon=True).start()
    threading.Thread(target=food_spawning_loop, daemon=True).start()

def initialize_simulation():
    """Generate some initial creatures for testing."""
    with Creature.creatures_lock:

        Creature.creatures.append(Creature(position=[100, 250], organs=[
            {"type": "flipper", "position": [-30, 0], "size": 5},
            {"type": "mouth", "position": [25, 0], "size": 5},
            {"type": "spike", "position": [0, 20], "size": 5}
            
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

        Creature.creatures.append(Creature(position=[400, 400], organs=[
            {"type": "flipper", "position": [-30, 0], "size": 5},
            {"type": "mouth", "position": [25, 0], "size": 5}
        ]))
        

    if PRINT: print(f"✅ Initialized {len(Creature.creatures)} creatures.")
