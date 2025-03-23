import threading
from .cell import Cell

# world.py
food = []
food_lock = threading.Lock()
creatures = []
creatures_lock = threading.Lock()
cell_grid = None