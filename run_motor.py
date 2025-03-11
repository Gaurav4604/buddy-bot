import Jetson.GPIO as GPIO
import time
import keyboard  # pip install keyboard

# Pin Definitions
# Left Side Motors
ENA_LEFT = 32  # PWM for Left Side Motors
IN1_LEFT = 12  # Left Motor 1 Forward
IN2_LEFT = 11  # Left Motor 1 Backward
IN3_LEFT = 22  # Left Motor 2 Forward
IN4_LEFT = 21  # Left Motor 2 Backward

# Right Side Motors
ENA_RIGHT = 33  # PWM for Right Side Motors
IN1_RIGHT = 15  # Right Motor 1 Forward
IN2_RIGHT = 16  # Right Motor 1 Backward
IN3_RIGHT = 24  # Right Motor 2 Forward
IN4_RIGHT = 23  # Right Motor 2 Backward

# GPIO setup
GPIO.setmode(GPIO.BOARD)

# Setup PWM and Direction pins
GPIO.setup(ENA_LEFT, GPIO.OUT)
GPIO.setup(ENA_RIGHT, GPIO.OUT)
GPIO.setup(IN1_LEFT, GPIO.OUT)
GPIO.setup(IN2_LEFT, GPIO.OUT)
GPIO.setup(IN3_LEFT, GPIO.OUT)
GPIO.setup(IN4_LEFT, GPIO.OUT)
GPIO.setup(IN1_RIGHT, GPIO.OUT)
GPIO.setup(IN2_RIGHT, GPIO.OUT)
GPIO.setup(IN3_RIGHT, GPIO.OUT)
GPIO.setup(IN4_RIGHT, GPIO.OUT)

# Initialize hardware PWM on ENA pins at 1kHz frequency
pwm_left = GPIO.PWM(ENA_LEFT, 1000)
pwm_left.start(0)  # Start with 0% duty cycle
pwm_right = GPIO.PWM(ENA_RIGHT, 1000)
pwm_right.start(0)


# Movement Functions
def move_forward(speed):
    """Move forward with the same speed on both sides."""
    # Set all motors to forward
    GPIO.output(IN1_LEFT, GPIO.HIGH)
    GPIO.output(IN2_LEFT, GPIO.LOW)
    GPIO.output(IN3_LEFT, GPIO.HIGH)
    GPIO.output(IN4_LEFT, GPIO.LOW)
    GPIO.output(IN1_RIGHT, GPIO.HIGH)
    GPIO.output(IN2_RIGHT, GPIO.LOW)
    GPIO.output(IN3_RIGHT, GPIO.HIGH)
    GPIO.output(IN4_RIGHT, GPIO.LOW)
    pwm_left.ChangeDutyCycle(speed)
    pwm_right.ChangeDutyCycle(speed)


def move_backward(speed):
    """Move backward with the same speed on both sides."""
    GPIO.output(IN1_LEFT, GPIO.LOW)
    GPIO.output(IN2_LEFT, GPIO.HIGH)
    GPIO.output(IN3_LEFT, GPIO.LOW)
    GPIO.output(IN4_LEFT, GPIO.HIGH)
    GPIO.output(IN1_RIGHT, GPIO.LOW)
    GPIO.output(IN2_RIGHT, GPIO.HIGH)
    GPIO.output(IN3_RIGHT, GPIO.LOW)
    GPIO.output(IN4_RIGHT, GPIO.HIGH)
    pwm_left.ChangeDutyCycle(speed)
    pwm_right.ChangeDutyCycle(speed)


def turn_left(speed):
    """Turn left in place."""
    # Reverse left motors, forward right motors
    GPIO.output(IN1_LEFT, GPIO.LOW)
    GPIO.output(IN2_LEFT, GPIO.HIGH)
    GPIO.output(IN3_LEFT, GPIO.LOW)
    GPIO.output(IN4_LEFT, GPIO.HIGH)
    GPIO.output(IN1_RIGHT, GPIO.HIGH)
    GPIO.output(IN2_RIGHT, GPIO.LOW)
    GPIO.output(IN3_RIGHT, GPIO.HIGH)
    GPIO.output(IN4_RIGHT, GPIO.LOW)
    pwm_left.ChangeDutyCycle(speed)
    pwm_right.ChangeDutyCycle(speed)


def turn_right(speed):
    """Turn right in place."""
    # Forward left motors, reverse right motors
    GPIO.output(IN1_LEFT, GPIO.HIGH)
    GPIO.output(IN2_LEFT, GPIO.LOW)
    GPIO.output(IN3_LEFT, GPIO.HIGH)
    GPIO.output(IN4_LEFT, GPIO.LOW)
    GPIO.output(IN1_RIGHT, GPIO.LOW)
    GPIO.output(IN2_RIGHT, GPIO.HIGH)
    GPIO.output(IN3_RIGHT, GPIO.LOW)
    GPIO.output(IN4_RIGHT, GPIO.HIGH)
    pwm_left.ChangeDutyCycle(speed)
    pwm_right.ChangeDutyCycle(speed)


def move_forward_left():
    """Move forward with a left bias: left motors at 100%, right motors at 80%."""
    GPIO.output(IN1_LEFT, GPIO.HIGH)
    GPIO.output(IN2_LEFT, GPIO.LOW)
    GPIO.output(IN3_LEFT, GPIO.HIGH)
    GPIO.output(IN4_LEFT, GPIO.LOW)
    GPIO.output(IN1_RIGHT, GPIO.HIGH)
    GPIO.output(IN2_RIGHT, GPIO.LOW)
    GPIO.output(IN3_RIGHT, GPIO.HIGH)
    GPIO.output(IN4_RIGHT, GPIO.LOW)
    pwm_left.ChangeDutyCycle(100)
    pwm_right.ChangeDutyCycle(80)


def move_forward_right():
    """Move forward with a right bias: left motors at 80%, right motors at 100%."""
    GPIO.output(IN1_LEFT, GPIO.HIGH)
    GPIO.output(IN2_LEFT, GPIO.LOW)
    GPIO.output(IN3_LEFT, GPIO.HIGH)
    GPIO.output(IN4_LEFT, GPIO.LOW)
    GPIO.output(IN1_RIGHT, GPIO.HIGH)
    GPIO.output(IN2_RIGHT, GPIO.LOW)
    GPIO.output(IN3_RIGHT, GPIO.HIGH)
    GPIO.output(IN4_RIGHT, GPIO.LOW)
    pwm_left.ChangeDutyCycle(80)
    pwm_right.ChangeDutyCycle(100)


def stop_motors():
    """Stop all motors."""
    GPIO.output(IN1_LEFT, GPIO.LOW)
    GPIO.output(IN2_LEFT, GPIO.LOW)
    GPIO.output(IN3_LEFT, GPIO.LOW)
    GPIO.output(IN4_LEFT, GPIO.LOW)
    GPIO.output(IN1_RIGHT, GPIO.LOW)
    GPIO.output(IN2_RIGHT, GPIO.LOW)
    GPIO.output(IN3_RIGHT, GPIO.LOW)
    GPIO.output(IN4_RIGHT, GPIO.LOW)
    pwm_left.ChangeDutyCycle(0)
    pwm_right.ChangeDutyCycle(0)


# Main loop to process keyboard input
print("Control the robot with:")
print("   w: forward")
print("   s: backward")
print("   a: turn left")
print("   d: turn right")
print("   wa: forward with left bias")
print("   wd: forward with right bias")
print("   space: stop motors")
print("Press Ctrl+C to exit.")

try:
    while True:
        # Stop if space is pressed
        if keyboard.is_pressed("space"):
            stop_motors()
            print("Stopping motors")
            time.sleep(0.1)
        # Forward with bias to the left if 'w' and 'a' are pressed together
        elif keyboard.is_pressed("w") and keyboard.is_pressed("a"):
            move_forward_left()
            print("Moving forward with left bias")
            time.sleep(0.1)
        # Forward with bias to the right if 'w' and 'd' are pressed together
        elif keyboard.is_pressed("w") and keyboard.is_pressed("d"):
            move_forward_right()
            print("Moving forward with right bias")
            time.sleep(0.1)
        # Regular forward
        elif keyboard.is_pressed("w"):
            move_forward(100)
            print("Moving forward")
            time.sleep(0.1)
        # Regular backward
        elif keyboard.is_pressed("s"):
            move_backward(100)
            print("Moving backward")
            time.sleep(0.1)
        # Turn left in place
        elif keyboard.is_pressed("a"):
            turn_left(100)
            print("Turning left")
            time.sleep(0.1)
        # Turn right in place
        elif keyboard.is_pressed("d"):
            turn_right(100)
            print("Turning right")
            time.sleep(0.1)
        else:
            # If no key is pressed, stop the motors
            stop_motors()
            time.sleep(0.1)
except KeyboardInterrupt:
    print("Exiting program")
finally:
    pwm_left.stop()
    pwm_right.stop()
    GPIO.cleanup()
