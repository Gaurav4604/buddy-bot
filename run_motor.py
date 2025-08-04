import Jetson.GPIO as GPIO
import time

# --- Pin Definitions ---

# Direction Pins (as per your original layout)
# Left Side Motors
IN1_LEFT = 12  # Left Motor 1 Forward
IN2_LEFT = 11  # Left Motor 1 Backward
IN3_LEFT = 22  # Left Motor 2 Forward
IN4_LEFT = 21  # Left Motor 2 Backward

# Right Side Motors
IN1_RIGHT = 15  # Right Motor 1 Forward
IN2_RIGHT = 16  # Right Motor 1 Backward
IN3_RIGHT = 24  # Right Motor 2 Forward
IN4_RIGHT = 23  # Right Motor 2 Backward

# PWM Enable Pins (for speed control)
# These connect to the ENA and ENB pins on the L298N drivers
ENA_LEFT_1 = 35  # PWM for Left Motor 1
ENB_LEFT_2 = 36  # PWM for Left Motor 2
ENA_RIGHT_1 = 37  # PWM for Right Motor 1
ENB_RIGHT_2 = 38  # PWM for Right Motor 2

# --- GPIO Setup ---
GPIO.setmode(GPIO.BOARD)

# Combine all pins for easy setup
direction_pins = [
    IN1_LEFT,
    IN2_LEFT,
    IN3_LEFT,
    IN4_LEFT,
    IN1_RIGHT,
    IN2_RIGHT,
    IN3_RIGHT,
    IN4_RIGHT,
]
pwm_pins = [ENA_LEFT_1, ENB_LEFT_2, ENA_RIGHT_1, ENB_RIGHT_2]
all_pins = direction_pins + pwm_pins

for pin in all_pins:
    GPIO.setup(pin, GPIO.OUT)

# --- PWM Initialization ---
# Create PWM objects for each enable pin with a frequency of 100Hz
pwm_left_1 = GPIO.PWM(ENA_LEFT_1, 100)
pwm_left_2 = GPIO.PWM(ENB_LEFT_2, 100)
pwm_right_1 = GPIO.PWM(ENA_RIGHT_1, 100)
pwm_right_2 = GPIO.PWM(ENB_RIGHT_2, 100)

# Group PWM objects for easy control
pwms = [pwm_left_1, pwm_left_2, pwm_right_1, pwm_right_2]

# --- Movement & Speed Functions ---


def move_forward():
    """Sets all motors to a forward direction."""
    print("Setting motor direction to FORWARD")
    # Left Motors Forward
    GPIO.output(IN1_LEFT, GPIO.HIGH)
    GPIO.output(IN2_LEFT, GPIO.LOW)
    GPIO.output(IN3_LEFT, GPIO.HIGH)
    GPIO.output(IN4_LEFT, GPIO.LOW)
    # Right Motors Forward
    GPIO.output(IN1_RIGHT, GPIO.HIGH)
    GPIO.output(IN2_RIGHT, GPIO.LOW)
    GPIO.output(IN3_RIGHT, GPIO.HIGH)
    GPIO.output(IN4_RIGHT, GPIO.LOW)


def set_all_motors_speed(speed):
    """Sets the speed for all motors."""
    # Duty cycle is a percentage from 0 to 100
    if not 0 <= speed <= 100:
        print("Speed must be between 0 and 100")
        return
    for pwm in pwms:
        pwm.ChangeDutyCycle(speed)


def stop_motors():
    """Stops all motors by disabling direction and PWM."""
    print("Stopping all motors.")
    # Set direction pins to LOW (coast)
    for pin in direction_pins:
        GPIO.output(pin, GPIO.LOW)
    # Set speed to 0
    set_all_motors_speed(0)


# --- Main Execution ---

if __name__ == "__main__":
    try:
        print("Starting motor PWM speed control test...")

        # Start all PWM channels with 0% duty cycle (motors off)
        for pwm in pwms:
            pwm.start(0)

        # Set the direction for the motors to move forward
        move_forward()
        time.sleep(1)  # Pause for a second

        # Ramp up the speed from 10% to 100%
        for speed in range(10, 101, 10):
            print(f"Setting speed to {speed}%")
            set_all_motors_speed(speed)
            time.sleep(2)  # Run at this speed for 2 seconds

        print("\nSpeed ramp test complete.")
        time.sleep(2)

    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Gracefully stop motors and clean up GPIO resources
        stop_motors()
        for pwm in pwms:
            pwm.stop()
        GPIO.cleanup()
        print("GPIO cleaned up and script finished.")
