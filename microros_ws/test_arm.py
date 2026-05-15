import time
from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685

# --- CONFIGURATION ---
i2c = busio.I2C(SCL, SDA)
pca = PCA9685(i2c)
pca.frequency = 50  # Standard Servo Frequency

# Servo Pulse Widths (Calibration)
MIN_PULSE = 500
MAX_PULSE = 2500

# Channel Setup
SERVOS = {
    0: "Base (12V)",
    1: "Shoulder (12V)",
    2: "Elbow (12V)",
    3: "Gripper (6V)" 
}

def get_duty_cycle(pulse_us):
    """Converts pulse width (us) to 16-bit duty cycle for PCA9685"""
    duty = int((pulse_us / 20000.0) * 65535)
    return duty

def angle_to_pulse(angle, max_angle=270):
    """Maps 0-MaxAngle to MIN_PULSE-MAX_PULSE"""
    angle = max(0, min(angle, max_angle))
    pulse = MIN_PULSE + (angle / max_angle) * (MAX_PULSE - MIN_PULSE)
    return pulse

def move_servo(channel, angle):
    name = SERVOS.get(channel, "Unknown")
    
    # Gripper is 180 degrees, others are 270 degrees
    max_ang = 180 if channel == 3 else 270
    
    pulse_us = angle_to_pulse(angle, max_ang)
    duty = get_duty_cycle(pulse_us)
    
    print(f"Moving {name} [Ch {channel}] to {angle}°")
    pca.channels[channel].duty_cycle = duty

# --- MAIN LOOP ---
print("--- ARM TEST MODE (FAST) ---")
print("Available Channels:")
for ch, name in SERVOS.items():
    print(f"  {ch}: {name}")

try:
    while True:
        try:
            user_input = input("\nEnter 'channel angle' (e.g., '0 90'): ")
            if user_input.lower() in ['q', 'quit', 'exit']:
                break
                
            parts = user_input.split()
            if len(parts) != 2:
                print("Invalid format. Use: Channel Angle")
                continue
                
            ch = int(parts[0])
            ang = float(parts[1])
            
            if ch not in SERVOS:
                print(f"Invalid Channel! Use 0, 1, 2, or 3.")
                continue

            # Execute move immediately
            move_servo(ch, ang)
            
        except ValueError:
            print("Please enter numbers only.")

except KeyboardInterrupt:
    print("\nExiting...")
    # Release servos
    for i in range(4):
        pca.channels[i].duty_cycle = 0
    print("Motors Released.")