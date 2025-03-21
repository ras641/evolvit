import threading

class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.creatures = []
        self.food = []
        self.lock = threading.Lock()