import time

def main_loop():
    target_fps = 20  # 10 frames per second
    target_interval = 1.0 / target_fps  # Target time per frame (in seconds)
    
    while True:
        frame_start_time = time.time()  # Get the start time of the frame
        
        # Main loop code: This is where your game logic, rendering, or processing happens
        print("Frame rendered")
        
        # Measure the time it took to run the loop
        frame_duration = time.time() - frame_start_time
        
        # Calculate how long to sleep to maintain the desired FPS
        sleep_time = target_interval - frame_duration
        
        if sleep_time > 0:
            # Sleep for the remaining time to maintain the target FPS
            time.sleep(sleep_time)

if __name__ == "__main__":
    main_loop()
