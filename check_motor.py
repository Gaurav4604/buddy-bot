import Jetson.GPIO as GPIO
import time
import sys

# Pin Definitions
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

# PWM Pins
ENA_LEFT = 32  # PWM for Left Side Motors
ENA_RIGHT = 33  # PWM for Right Side Motors

# GPIO setup
GPIO.setmode(GPIO.BOARD)

# Setup PWM and Direction Pins
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

# Initialize hardware PWM
pwm_left = GPIO.PWM(ENA_LEFT, 1000)  # Left Motors PWM
pwm_left.start(0)

pwm_right = GPIO.PWM(ENA_RIGHT, 1000)  # Right Motors PWM
pwm_right.start(0)


# Motor Control Functions
def motor_forward(pwm, in1, in2, speed):
    GPIO.output(in1, GPIO.HIGH)
    GPIO.output(in2, GPIO.LOW)
    pwm.ChangeDutyCycle(speed)


def motor_backward(pwm, in1, in2, speed):
    GPIO.output(in1, GPIO.LOW)
    GPIO.output(in2, GPIO.HIGH)
    pwm.ChangeDutyCycle(speed)


def motor_stop(in1, in2):
    GPIO.output(in1, GPIO.LOW)
    GPIO.output(in2, GPIO.LOW)


# Main Function
def test_motor(motor_id):
    speed = 75  # Test speed (75% duty cycle)

    if motor_id == 1:
        print("Testing Motor 1 (Left Motor 1)")
        motor_forward(pwm_left, IN1_LEFT, IN2_LEFT, speed)
        time.sleep(5)
        motor_backward(pwm_left, IN1_LEFT, IN2_LEFT, speed)
        time.sleep(5)
        motor_stop(IN1_LEFT, IN2_LEFT)

    elif motor_id == 2:
        print("Testing Motor 2 (Left Motor 2)")
        motor_forward(pwm_left, IN3_LEFT, IN4_LEFT, speed)
        time.sleep(5)
        motor_backward(pwm_left, IN3_LEFT, IN4_LEFT, speed)
        time.sleep(5)
        motor_stop(IN3_LEFT, IN4_LEFT)

    elif motor_id == 3:
        print("Testing Motor 3 (Right Motor 1)")
        motor_forward(pwm_right, IN1_RIGHT, IN2_RIGHT, speed)
        time.sleep(5)
        motor_backward(pwm_right, IN1_RIGHT, IN2_RIGHT, speed)
        time.sleep(5)
        motor_stop(IN1_RIGHT, IN2_RIGHT)

    elif motor_id == 4:
        print("Testing Motor 4 (Right Motor 2)")
        motor_forward(pwm_right, IN3_RIGHT, IN4_RIGHT, speed)
        time.sleep(5)
        motor_backward(pwm_right, IN3_RIGHT, IN4_RIGHT, speed)
        time.sleep(5)
        motor_stop(IN3_RIGHT, IN4_RIGHT)

    else:
        print("Invalid motor ID. Please specify 1, 2, 3, or 4.")
        return


# Entry Point
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 check_motor.py <motor_id>")
        print(
            "  <motor_id>: 1 (Left Motor 1), 2 (Left Motor 2), 3 (Right Motor 1), or 4 (Right Motor 2)"
        )
        sys.exit(1)

    try:
        motor_id = int(sys.argv[1])
        test_motor(motor_id)

    except ValueError:
        print("Invalid motor ID. Please specify 1, 2, 3, or 4.")

    except KeyboardInterrupt:
        print("Exiting program")

    finally:
        pwm_left.stop()
        pwm_right.stop()
        GPIO.cleanup()

