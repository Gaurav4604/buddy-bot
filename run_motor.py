import curses
import time
import asyncio
import json
import Jetson.GPIO as GPIO
from buddy_bot_communication.client import Node

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
pins = [
    ENA_LEFT,
    ENA_RIGHT,
    IN1_LEFT,
    IN2_LEFT,
    IN3_LEFT,
    IN4_LEFT,
    IN1_RIGHT,
    IN2_RIGHT,
    IN3_RIGHT,
    IN4_RIGHT,
]
for pin in pins:
    GPIO.setup(pin, GPIO.OUT)

# Initialize hardware PWM on ENA pins at 1kHz frequency
pwm_left = GPIO.PWM(ENA_LEFT, 1000)
pwm_left.start(0)
pwm_right = GPIO.PWM(ENA_RIGHT, 1000)
pwm_right.start(0)


# Movement Functions
def move_forward(speed):
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


class RobotController:
    def __init__(self):
        # Track active control keys
        self.active_keys = set()
        self.speed = 100

    def handle_command(self, command_data):
        """Handle incoming command from websocket"""
        command = command_data.get("command")
        status = command_data.get("status")

        # Update active keys set
        if status == "down":
            self.active_keys.add(command)
        elif status == "release":
            self.active_keys.discard(command)

        # Apply movement based on active keys
        self.update_movement()

    def update_movement(self):
        """Update robot movement based on currently active keys"""
        if not self.active_keys:
            stop_motors()
            return

        # Priority: if multiple keys are pressed, choose one based on priority
        if "w" in self.active_keys:
            move_forward(self.speed)
        elif "s" in self.active_keys:
            move_backward(self.speed)
        elif "a" in self.active_keys:
            turn_left(self.speed)
        elif "d" in self.active_keys:
            turn_right(self.speed)
        else:
            stop_motors()


async def control_handler(data, robot_controller):
    """Handle incoming control commands"""
    try:
        command_data = json.loads(data)
        print(f"Received: {command_data}")
        robot_controller.handle_command(command_data)
    except json.JSONDecodeError:
        print(f"Invalid JSON data: {data}")
    except Exception as e:
        print(f"Error handling command: {e}")


async def main():
    robot_controller = RobotController()
    node = Node("http://172.22.7.122:7000")

    try:
        await node.connect()
        print("Connected to server")

        # Create a partial function to pass the robot_controller
        handler = lambda data: control_handler(data, robot_controller)

        # Subscribe to control topic
        await node.subscribe("/control", handler)

        # Keep the program running
        while True:
            await asyncio.sleep(0.1)

    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Shutting down gracefully...")
    except Exception as e:
        print(f"Error in main loop: {e}")
    finally:
        # Clean up
        stop_motors()
        pwm_left.stop()
        pwm_right.stop()
        GPIO.cleanup()
        await node.disconnect()
        print("Disconnected and cleaned up")


if __name__ == "__main__":
    asyncio.run(main())
