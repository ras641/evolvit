import random
import time
import threading
import traceback
import math
import simulation.config as config


class Food:
    def __init__(self, position):
        self.position = position

    def to_dict(self):
        return self.position


def food_spawning_loop(world):

    time.sleep(1)

    cell = world.cell_grid[0][0]

    while True:
        if len(cell.food) < config.MAX_FOOD:

            new_food = Food(position=[
                random.randint(0, 499),
                random.randint(0, 499)
            ])
            
            with cell.lock:
                cell.add(new_food)

        time.sleep(0.05 * (len(cell.creatures) ** 1.5) * (30/config.FPS))

def food_spawning_loop2():
    return
    import simulation.simulation.world as world

    food_spawn_accumulator = 0.0
    loop_counter = 0

    while True:
        try:
            # ✅ Accumulate spawn potential
            food_spawn_accumulator += 10
            spawn_count = int(food_spawn_accumulator)
            food_spawn_accumulator -= spawn_count

            new_food_list = []

            # ✅ Create food objects without holding locks
            for _ in range(spawn_count):
                if len(world.food) >= config.MAX_FOOD:
                    break

                new_food = Food(position=[
                    random.randint(0, 499),
                    random.randint(0, 499)
                ])
                new_food_list.append(new_food)

            # ✅ Append to global food list (quick lock)
            if new_food_list:
                with world.food_lock:
                    world.food.extend(new_food_list)

            # ✅ Add to cell (separately)
            for food_obj in new_food_list:
                try:
                    if world.cell_grid:
                        x = min(int(food_obj.position[0] // 50), len(world.cell_grid) - 1)
                        y = min(int(food_obj.position[1] // 50), len(world.cell_grid[0]) - 1)
                        cell = world.cell_grid[x][y]
                        with cell.lock:
                            cell.add(food_obj)
                            food_obj.cell = cell
                    else:
                        print("⚠️ cell_grid not initialized yet")
                except Exception as e:
                    print(f"❌ Error adding food to cell: {e}")
                    traceback.print_exc()

            # ✅ Print every second
            loop_counter += 1
            if loop_counter % 10 == 0:
                print(f"🍏 Total food: {len(world.food)}")

        except Exception as e:
            print("🔥 CRITICAL: food_spawning_loop crashed")
            traceback.print_exc()

        time.sleep(0.1)

