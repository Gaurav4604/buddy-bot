import curses
import time
import Jetson.GPIO as GPIO

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


def move_forward_left():
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


def main(stdscr):
    # Curses setup
    curses.noecho()
    curses.cbreak()
    stdscr.nodelay(True)  # non-blocking input
    stdscr.keypad(True)

    stdscr.addstr(0, 0, "Control the robot with WASD and space; ESC to exit")

    # Main loop: poll for key press
    while True:
        c = stdscr.getch()
        # Clear previous feedback
        stdscr.move(1, 0)
        stdscr.clrtoeol()

        if c != -1:
            if c == 27:  # ESC key
                stdscr.addstr(1, 0, "Exiting program")
                stdscr.refresh()
                break
            elif c in (ord("w"), ord("W")):
                # For simplicity, we'll only check one key at a time
                stdscr.addstr(1, 0, "Moving forward")
                move_forward(100)
            elif c in (ord("s"), ord("S")):
                stdscr.addstr(1, 0, "Moving backward")
                move_backward(100)
            elif c in (ord("a"), ord("A")):
                stdscr.addstr(1, 0, "Turning left")
                turn_left(100)
            elif c in (ord("d"), ord("D")):
                stdscr.addstr(1, 0, "Turning right")
                turn_right(100)
            elif c == ord(" "):
                stdscr.addstr(1, 0, "Stopping motors")
                stop_motors()
        else:
            # No key pressed; stop motors by default
            stop_motors()

        stdscr.refresh()
        time.sleep(0.05)


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("Exiting program (KeyboardInterrupt)")
    finally:
        pwm_left.stop()
        pwm_right.stop()
        GPIO.cleanup()
