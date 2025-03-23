import creatures

import threading

class SpatialGrid:
    def __init__(self, width, height, cell_size):
        self.cell_size = cell_size
        self.cols = width // cell_size
        self.rows = height // cell_size
        self.grid = [[[] for _ in range(self.cols)] for _ in range(self.rows)]
        self.lock = threading.Lock()