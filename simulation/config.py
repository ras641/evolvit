

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR) 

frame_count = 0

BODY_RADIUS = 8

PRINT = 0

SVG = False

# Simulation Settings

FPS = 30.0
SIMULATION_SPEED = 0
if FPS > 0: SIMULATION_SPEED = 1.0/FPS
BASE_REPRODUCTION_CHANCE = 0.05
REPRODUCE = True
MAX_AV = 2 #radians per frame
BMR = 0.01 #energy per frame

# Food Settings
MAX_FOOD = 200
#FOOD_SPAWN_INTERVAL = 40
FOOD_STEP = 0.01

#Physics
FRICTION = 0.99
ANGULAR_FRICTION = 0.95
FRICTION_STEP = 5

DEBUG = False