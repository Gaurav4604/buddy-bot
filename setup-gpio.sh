# Enable Pin 32 (PWM0)
sudo busybox devmem 0x700031fc 32 0x45
sudo busybox devmem 0x6000d504 32 0x2

# Enable Pin 33 (PWM2)
sudo busybox devmem 0x70003248 32 0x46
sudo busybox devmem 0x6000d100 32 0x00

# Verify the presence of the PWM chip
ls /sys/class/pwm/pwmchip0

# Export PWM0 (for Pin 32)
echo 0 | sudo tee /sys/class/pwm/pwmchip0/export
# Export PWM2 (for Pin 33)
echo 1 | sudo tee /sys/class/pwm/pwmchip0/export

# Set PWM0 (Pin 32) period and duty cycle
echo 1000000 | sudo tee /sys/class/pwm/pwmchip0/pwm0/period   # Set period to 1ms (1kHz frequency)
echo 0       | sudo tee /sys/class/pwm/pwmchip0/pwm0/duty_cycle # Set initial duty cycle to 0%
echo 1       | sudo tee /sys/class/pwm/pwmchip0/pwm0/enable   # Enable PWM0

# Set PWM2 (Pin 33) period and duty cycle
echo 1000000 | sudo tee /sys/class/pwm/pwmchip0/pwm1/period   # Set period to 1ms (1kHz frequency)
echo 0       | sudo tee /sys/class/pwm/pwmchip0/pwm1/duty_cycle # Set initial duty cycle to 0%
echo 1       | sudo tee /sys/class/pwm/pwmchip0/pwm1/enable   # Enable PWM2

