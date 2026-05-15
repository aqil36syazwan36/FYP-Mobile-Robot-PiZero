import time
import board
import busio
import pigpio
from adafruit_pca9685 import PCA9685

# --- ROBOT CONFIGURATION ---
WHEEL_DIAMETER_MM = 130.0
# Based on your test result of ~95cm avg, 1000 ticks is a very good calibration.
TICKS_PER_REV = 1000.0 
CIRCUMFERENCE_CM = (WHEEL_DIAMETER_MM * 3.14159) / 10.0

# --- PCA9685 SETUP ---
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 60

# --- MOTOR CHANNEL MAPPING (0-15) ---
# RB and RF IN1/IN2 are swapped relative to standard to match your wiring
MOTORS = {
    "RB": {"EN": 15, "IN1": 13, "IN2": 14}, 
    "RF": {"EN": 10, "IN1": 12, "IN2": 11}, 
    "LB": {"EN": 9,  "IN1": 8,  "IN2": 7},
    "LF": {"EN": 4,  "IN1": 5,  "IN2": 6} 
}

# --- ENCODER CLASS ---
class Encoder:
    def __init__(self, pi, gpio_a, gpio_b, name, reverse=False):
        self.pi = pi
        self.name = name
        self.reverse = reverse
        self.count = 0
        self.levA = 0
        self.levB = 0
        
        # Save pin numbers so _pulse can use them
        self.gpio_a = gpio_a
        self.gpio_b = gpio_b
        
        pi.set_mode(gpio_a, pigpio.INPUT)
        pi.set_pull_up_down(gpio_a, pigpio.PUD_UP)
        pi.set_mode(gpio_b, pigpio.INPUT)
        pi.set_pull_up_down(gpio_b, pigpio.PUD_UP)
        
        self.cb_a = pi.callback(gpio_a, pigpio.EITHER_EDGE, self._pulse)
        self.cb_b = pi.callback(gpio_b, pigpio.EITHER_EDGE, self._pulse)

    def _pulse(self, gpio, level, tick):
        if gpio == self.gpio_a: self.levA = level
        else: self.levB = level
        
        if gpio == self.gpio_a and level == 1:
            change = 1 if self.levB == 0 else -1
        elif gpio == self.gpio_a and level == 0:
            change = 1 if self.levB == 1 else -1
        else:
            return

        self.count += (change * -1 if self.reverse else change)

    def get_distance(self):
        return (self.count / TICKS_PER_REV) * CIRCUMFERENCE_CM

# --- MOTOR CONTROL ---
def set_speed(motor_key, speed, forward=True):
    m = MOTORS[motor_key]
    duty = int(abs(speed) * 655.35)
    pca.channels[m["EN"]].duty_cycle = duty
    if forward:
        pca.channels[m["IN1"]].duty_cycle = 65535
        pca.channels[m["IN2"]].duty_cycle = 0
    else:
        pca.channels[m["IN1"]].duty_cycle = 0
        pca.channels[m["IN2"]].duty_cycle = 65535

def stop():
    for m in MOTORS.values():
        pca.channels[m["EN"]].duty_cycle = 0

# --- MAIN EXECUTION ---
pi = pigpio.pi()

# FINAL CONFIGURATION
# RB: Fixed to True (was -105.7cm)
# RF: True (was 95.6cm)
# LB: False (was 114.9cm)
# LF: False (was 82.2cm)
encoders = {
    "RB": Encoder(pi, 17, 27, "RB", reverse=True), 
    "RF": Encoder(pi, 22, 23, "RF", reverse=True),  
    "LB": Encoder(pi, 24, 25, "LB", reverse=False), 
    "LF": Encoder(pi, 5, 6, "LF", reverse=False)    
}

try:
    print("Driving Forward for 100cm...")
    target_cm = 100.0
    
    # 40% Speed is safe for testing
    TEST_SPEED = 40 
    
    while True:
        # Calculate average distance (using absolute values to prevent glitches)
        avg_dist = sum([abs(e.get_distance()) for e in encoders.values()]) / 4.0
        
        if avg_dist < target_cm:
            for key in MOTORS: set_speed(key, TEST_SPEED)
        else:
            stop()
            print("\nTarget Reached!")
            break
            
        status = " | ".join([f"{k}: {e.get_distance():.1f}cm" for k, e in encoders.items()])
        print(f"\r{status} | Avg: {avg_dist:.1f}cm", end="", flush=True)
        time.sleep(0.05)

except KeyboardInterrupt:
    stop()
    pi.stop()