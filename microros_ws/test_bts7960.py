import time
import board
import busio
from adafruit_pca9685 import PCA9685

# --- SETUP PCA9685 ---
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 60

# --- CONFIGURATION ---
# You connected these to Channel 12 and 13
PIN_FWD = 12  # RPWM
PIN_REV = 13  # LPWM

def set_speed(speed_percent):
    """
    speed_percent: -100 to 100
    """
    # Safety clamp
    speed_percent = max(min(speed_percent, 100), -100)
    
    # Convert to 16-bit duty cycle (0-65535)
    duty = int(abs(speed_percent) * 655.35)
    
    if speed_percent > 0:
        # FORWARD: RPWM gets signal, LPWM is 0
        pca.channels[PIN_FWD].duty_cycle = duty
        pca.channels[PIN_REV].duty_cycle = 0
        print(f"Driving FORWARD at {speed_percent}% (Channel {PIN_FWD})")
        
    elif speed_percent < 0:
        # REVERSE: LPWM gets signal, RPWM is 0
        pca.channels[PIN_FWD].duty_cycle = 0
        pca.channels[PIN_REV].duty_cycle = duty
        print(f"Driving REVERSE at {speed_percent}% (Channel {PIN_REV})")
        
    else:
        # STOP
        pca.channels[PIN_FWD].duty_cycle = 0
        pca.channels[PIN_REV].duty_cycle = 0
        print("STOPPED")

try:
    print("--- BTS7960 MOTOR TEST ---")
    print("1. Checking Connections...")
    set_speed(0)
    time.sleep(1)

    print("\n2. Ramping Up FORWARD...")
    for s in range(0, 101, 10): # 0, 10, 20... 100
        set_speed(s)
        time.sleep(0.5)
    
    time.sleep(1)
    set_speed(0)
    time.sleep(1)

    print("\n3. Ramping Up REVERSE...")
    for s in range(0, -101, -10): # 0, -10, -20... -100
        set_speed(s)
        time.sleep(0.5)

    set_speed(0)
    print("\n--- TEST COMPLETE ---")

except KeyboardInterrupt:
    set_speed(0)
    print("\nSafety Stop!")