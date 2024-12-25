import Jetson.GPIO as GPIO
import time

# Pin Definitions
ENA_PIN = 32  # GPIO07 / PWM0 (Pin 32)
IN1_PIN = 12  # GPIO18 (Pin 12)
IN2_PIN = 13  # GPIO27 (Pin 13)

# GPIO setup
GPIO.setmode(GPIO.BOARD)
GPIO.setup(IN1_PIN, GPIO.OUT)
GPIO.setup(IN2_PIN, GPIO.OUT)

# Initialize PWM on ENA_PIN
GPIO.setup(ENA_PIN, GPIO.OUT)  # Set ENA_PIN as output
pwm = GPIO.PWM(ENA_PIN, 1000)  # Create PWM object at 1kHz frequency
pwm.start(0)  # Start with 0% duty cycle

def set_motor_forward(speed):
    """Set motor to run forward at the specified speed (0-100)."""
    GPIO.output(IN1_PIN, GPIO.HIGH)
    GPIO.output(IN2_PIN, GPIO.LOW)
    pwm.ChangeDutyCycle(speed)

def set_motor_backward(speed):
    """Set motor to run backward at the specified speed (0-100)."""
    GPIO.output(IN1_PIN, GPIO.LOW)
    GPIO.output(IN2_PIN, GPIO.HIGH)
    pwm.ChangeDutyCycle(speed)

def stop_motor():
    """Stop the motor."""
    GPIO.output(IN1_PIN, GPIO.LOW)
    GPIO.output(IN2_PIN, GPIO.LOW)
    pwm.ChangeDutyCycle(0)

try:
    while True:
        # Run motor forward at 75% speed
        set_motor_forward(100)
        time.sleep(5)

        # Stop motor
        stop_motor()
        time.sleep(2)

        # Run motor backward at 50% speed
        set_motor_backward(100)
        time.sleep(5)

        # Stop motor
        stop_motor()
        time.sleep(2)

except KeyboardInterrupt:
    print("Exiting program")

finally:
    pwm.stop()
    GPIO.cleanup()

