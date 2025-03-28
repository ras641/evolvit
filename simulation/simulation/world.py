import threading
from .cell import Cell

class World:
    def __init__(self):
        self.frame = 0
        self.creatures = []
        self.creatures_lock = threading.RLock()

        self.food = []
        self.food_lock = threading.RLock()

        self.cell_grid = self._initialize_cells()
        self.built_index = None

    def _initialize_cells(self):
        grid = [[Cell(x, y) for x in range(10)] for y in range(10)]  # Or however you're partitioning
        for row in grid:
            for cell in row:
                cell.world = self  # Optional backref if needed
        return grid

    def get_frame(self):
        return self.frame

    def advance_frame(self):

        self.frame += 1
        
        if self.frame % Cell.BUFFER_FRAMES == 0:

            self.cell_grid[0][0].swap_buffers(self.frame)

            
            #for row in self.cell_grid:
            #    for cell in row:
            #        cell.swap_buffers(self.frame)

                # Optional per-frame simulation logic
                # cell.step(self.frame)

            self.built_index = self.frame - 300

        if (self.frame) == 300:

            print ("Buffered")

    def add_creature(self, creature):
        with self.creatures_lock:
            self.creatures.append(creature)

    def add_food(self, food_obj):
        with self.food_lock:
            self.food.append(food_obj)

    def get_state_for_cell(self, x, y):
        return self.cell_grid[y][x].get_state()
    
    def get_built_index(self):
        return self.built_index


world = World()