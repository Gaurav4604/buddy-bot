import Jetson.GPIO as GPIO
import time

# --- Pin Definitions ---
# It's crucial that these pin numbers match your main script.
# Left Side Motors
IN1_LEFT = 12
IN2_LEFT = 11
IN3_LEFT = 22
IN4_LEFT = 21

# Right Side Motors
IN1_RIGHT = 15
IN2_RIGHT = 16
IN3_RIGHT = 24
IN4_RIGHT = 23

# A list of all pins to be managed
ALL_PINS = [
    IN1_LEFT, IN2_LEFT, IN3_LEFT, IN4_LEFT,
    IN1_RIGHT, IN2_RIGHT, IN3_RIGHT, IN4_RIGHT,
]

def force_cleanup():
    """
    Safely stops all motors and cleans up GPIO resources.
    Run this script to reset the GPIO pins if the main control program
    crashes or exits without running its own cleanup routine.
    """
    print("--- Starting GPIO Cleanup Utility ---")
    
    # Use a try...finally block to ensure cleanup happens no matter what.
    try:
        # Set the pin numbering mode (must match your main script)
        GPIO.setmode(GPIO.BOARD)

        print(f"Targeting pins: {ALL_PINS}")

        # Explicitly set all motor control pins to LOW to stop the motors
        for pin in ALL_PINS:
            # We must configure the pin as an output before we can write to it
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

        print("All motor control pins have been set to LOW.")
        # A brief pause can be helpful in some hardware contexts
        time.sleep(0.1)

    except Exception as e:
        print(f"An error occurred during the process: {e}")
        print("Will proceed to the final cleanup step regardless.")

    finally:
        # This is the most important command.
        # It resets all GPIO channels that have been used back to their
        # default state (input), freeing them up for other programs.
        print("\nReleasing all GPIO resources...")
        GPIO.cleanup()
        print("--- Cleanup Complete ---")
        print("GPIO resources have been successfully released. ✅")


if __name__ == "__main__":
    force_cleanup()