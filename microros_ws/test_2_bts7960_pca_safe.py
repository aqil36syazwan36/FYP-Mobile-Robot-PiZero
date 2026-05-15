import time
import board
import busio
from adafruit_pca9685 import PCA9685

print("--- 2x BTS7960 + PCA9685 SAFE TEST ---")

i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 1000

# RIGHT BTS7960
RIGHT_RPWM = 12
RIGHT_LPWM = 13

# LEFT BTS7960
LEFT_RPWM = 9
LEFT_LPWM = 8

MAX_TEST_SPEED = 20  # safe first test

def stop_all():
    for ch in range(16):
        pca.channels[ch].duty_cycle = 0

def set_motor(rpwm_ch, lpwm_ch, speed_percent):
    speed_percent = max(min(speed_percent, 100), -100)
    duty = int(abs(speed_percent) / 100 * 65535)

    if speed_percent > 0:
        pca.channels[rpwm_ch].duty_cycle = duty
        pca.channels[lpwm_ch].duty_cycle = 0
    elif speed_percent < 0:
        pca.channels[rpwm_ch].duty_cycle = 0
        pca.channels[lpwm_ch].duty_cycle = duty
    else:
        pca.channels[rpwm_ch].duty_cycle = 0
        pca.channels[lpwm_ch].duty_cycle = 0

def set_right(speed):
    print(f"RIGHT speed: {speed}%")
    set_motor(RIGHT_RPWM, RIGHT_LPWM, speed)

def set_left(speed):
    print(f"LEFT speed: {speed}%")
    set_motor(LEFT_RPWM, LEFT_LPWM, speed)

try:
    print("PCA9685 connected.")
    print("Stopping all channels first...")
    stop_all()
    time.sleep(2)

    print("\nTesting RIGHT forward...")
    for s in range(0, MAX_TEST_SPEED + 1, 5):
        set_right(s)
        time.sleep(0.8)

    set_right(0)
    time.sleep(2)

    print("\nTesting RIGHT reverse...")
    for s in range(0, -MAX_TEST_SPEED - 1, -5):
        set_right(s)
        time.sleep(0.8)

    set_right(0)
    time.sleep(2)

    print("\nTesting LEFT forward...")
    for s in range(0, MAX_TEST_SPEED + 1, 5):
        set_left(s)
        time.sleep(0.8)

    set_left(0)
    time.sleep(2)

    print("\nTesting LEFT reverse...")
    for s in range(0, -MAX_TEST_SPEED - 1, -5):
        set_left(s)
        time.sleep(0.8)

    set_left(0)
    print("\n--- TEST COMPLETE ---")

except KeyboardInterrupt:
    print("\nKeyboard interrupt. Stopping motors...")

except Exception as e:
    print("ERROR:", e)

finally:
    stop_all()
    print("All PCA9685 channels stopped.")
