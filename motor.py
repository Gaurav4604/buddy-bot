import Jetson.GPIO as GPIO
import time

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

# PWM Pins
GPIO.setup(ENA_LEFT, GPIO.OUT)   # Enable Pin for Left Motors
GPIO.setup(ENA_RIGHT, GPIO.OUT)  # Enable Pin for Right Motors

# Left Side Direction Pins
GPIO.setup(IN1_LEFT, GPIO.OUT)
GPIO.setup(IN2_LEFT, GPIO.OUT)
GPIO.setup(IN3_LEFT, GPIO.OUT)
GPIO.setup(IN4_LEFT, GPIO.OUT)

# Right Side Direction Pins
GPIO.setup(IN1_RIGHT, GPIO.OUT)
GPIO.setup(IN2_RIGHT, GPIO.OUT)
GPIO.setup(IN3_RIGHT, GPIO.OUT)
GPIO.setup(IN4_RIGHT, GPIO.OUT)

# Initialize hardware PWM on ENA pins at 1kHz frequency
pwm_left = GPIO.PWM(ENA_LEFT, 1000)  # Left Motors PWM
pwm_left.start(0)  # Start with 0% duty cycle

pwm_right = GPIO.PWM(ENA_RIGHT, 1000)  # Right Motors PWM
pwm_right.start(0)

# Movement Functions
def move_forward(speed):
    """Move forward by running all motors forward."""
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
    """Move backward by running all motors backward."""
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
    """Turn left by reversing left motors and running right motors forward."""
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
    """Turn right by reversing right motors and running left motors forward."""
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

# Main Program
try:
    while True:
        print("Moving forward at 75% speed")
        move_forward(100)
        time.sleep(1)

        print("Moving backward at 75% speed")
        move_backward(100)
        time.sleep(1)

        print("Turning left at 75% speed")
        turn_left(75)
        time.sleep(3)

        print("Turning right at 75% speed")
        turn_right(75)
        time.sleep(3)

        print("Stopping motors")
        stop_motors()
        time.sleep(3)

except KeyboardInterrupt:
    print("Exiting program")

finally:
    pwm_left.stop()  # Stop Left PWM
    pwm_right.stop()  # Stop Right PWM
    GPIO.cleanup()  # Reset GPIO pins to default state

