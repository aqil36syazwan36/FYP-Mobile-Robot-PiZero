import time
import socket
import json
import board
import busio
import pigpio
from adafruit_pca9685 import PCA9685


# =========================
# NETWORK CONFIGURATION
# =========================
HOST = "0.0.0.0"
PORT = 65432


# =========================
# PCA9685 MOTOR CHANNELS
# =========================
# RIGHT BTS7960
RIGHT_RPWM = 12
RIGHT_LPWM = 13

# LEFT BTS7960
LEFT_RPWM = 9
LEFT_LPWM = 8

PCA_FREQ = 1000          # Better for DC motor PWM than 60 Hz
MAX_SPEED = 30           # Safety limit, percent
WATCHDOG_TIMEOUT = 1.0   # Stop motors if no command for 1 second

# Change these if motor direction is reversed
RIGHT_MOTOR_INVERT = 1
LEFT_MOTOR_INVERT = 1


# =========================
# ENCODER GPIO MAPPING
# =========================
# Corrected based on your physical wheel test
ENCODER_CONFIG = [
    {"name": "Right Back",  "a": 5,  "b": 6,  "invert": -1},
    {"name": "Right Front", "a": 24, "b": 25, "invert": -1},
    {"name": "Left Back",   "a": 22, "b": 23, "invert": 1},
    {"name": "Left Front",  "a": 17, "b": 27, "invert": 1},
]


# =========================
# ENCODER CLASS
# =========================
class Encoder:
    def __init__(self, pi, gpio_a, gpio_b, name, invert=1):
        self.pi = pi
        self.gpio_a = gpio_a
        self.gpio_b = gpio_b
        self.name = name
        self.invert = invert
        self.count = 0
        self.levA = 0
        self.levB = 0

        self.pi.set_mode(gpio_a, pigpio.INPUT)
        self.pi.set_pull_up_down(gpio_a, pigpio.PUD_UP)

        self.pi.set_mode(gpio_b, pigpio.INPUT)
        self.pi.set_pull_up_down(gpio_b, pigpio.PUD_UP)

        self.cb_a = self.pi.callback(gpio_a, pigpio.EITHER_EDGE, self._pulse)
        self.cb_b = self.pi.callback(gpio_b, pigpio.EITHER_EDGE, self._pulse)

    def _pulse(self, gpio, level, tick):
        if gpio == self.gpio_a:
            self.levA = level
        else:
            self.levB = level

        delta = 0

        if gpio == self.gpio_a and level == 1:
            delta = 1 if self.levB == 0 else -1

        elif gpio == self.gpio_a and level == 0:
            delta = 1 if self.levB == 1 else -1

        self.count += delta * self.invert

    def get_count(self):
        return self.count

    def reset(self):
        self.count = 0

    def cancel(self):
        self.cb_a.cancel()
        self.cb_b.cancel()


# =========================
# HELPER FUNCTIONS
# =========================
def clamp(value, low, high):
    return max(low, min(high, value))


def encoder_status(encoders):
    return {e.name: e.get_count() for e in encoders}


def stop_all_motors(pca):
    for ch in range(16):
        pca.channels[ch].duty_cycle = 0


def set_motor(pca, rpwm_ch, lpwm_ch, speed_percent):
    speed_percent = clamp(float(speed_percent), -MAX_SPEED, MAX_SPEED)
    duty = int(abs(speed_percent) / 100.0 * 65535)

    if speed_percent > 0:
        pca.channels[rpwm_ch].duty_cycle = duty
        pca.channels[lpwm_ch].duty_cycle = 0

    elif speed_percent < 0:
        pca.channels[rpwm_ch].duty_cycle = 0
        pca.channels[lpwm_ch].duty_cycle = duty

    else:
        pca.channels[rpwm_ch].duty_cycle = 0
        pca.channels[lpwm_ch].duty_cycle = 0


def set_drive(pca, right_speed, left_speed):
    right_speed = clamp(float(right_speed), -MAX_SPEED, MAX_SPEED)
    left_speed = clamp(float(left_speed), -MAX_SPEED, MAX_SPEED)

    motor_right = right_speed * RIGHT_MOTOR_INVERT
    motor_left = left_speed * LEFT_MOTOR_INVERT

    set_motor(pca, RIGHT_RPWM, RIGHT_LPWM, motor_right)
    set_motor(pca, LEFT_RPWM, LEFT_LPWM, motor_left)

    if abs(right_speed) > 0.1 or abs(left_speed) > 0.1:
        print(f"DRIVE right={right_speed:.1f}% left={left_speed:.1f}%")

    return right_speed, left_speed


def parse_drive(drive):
    """
    Accepted command formats:

    {"drive": [right, left]}

    or old 4-wheel format:

    {"drive": [right_back, right_front, left_back, left_front]}
    """

    if not isinstance(drive, list):
        raise ValueError("drive must be a list")

    if len(drive) == 2:
        right = float(drive[0])
        left = float(drive[1])
        return right, left

    if len(drive) == 4:
        right = (float(drive[0]) + float(drive[1])) / 2.0
        left = (float(drive[2]) + float(drive[3])) / 2.0
        return right, left

    raise ValueError("drive must be [right, left] or [RB, RF, LB, LF]")


def handle_command(cmd, pca, encoders):
    if cmd.get("ping") is not None:
        return {
            "status": "ok",
            "reply": "pong",
            "encoders": encoder_status(encoders)
        }

    if cmd.get("reset_encoders") is True:
        for e in encoders:
            e.reset()

        return {
            "status": "ok",
            "action": "reset_encoders",
            "encoders": encoder_status(encoders)
        }

    if cmd.get("stop") is True:
        stop_all_motors(pca)

        return {
            "status": "ok",
            "action": "stop",
            "encoders": encoder_status(encoders)
        }

    if "drive" in cmd:
        right, left = parse_drive(cmd["drive"])
        right, left = set_drive(pca, right, left)

        return {
            "status": "ok",
            "action": "drive",
            "right": right,
            "left": left,
            "encoders": encoder_status(encoders)
        }

    return {
        "status": "ok",
        "message": "no action",
        "encoders": encoder_status(encoders)
    }


# =========================
# MAIN
# =========================
def main():
    print("--- PI ZERO MOTOR SERVER ---")
    print("Motor only version: PCA9685 + 2x BTS7960 + encoders")

    print("Connecting to PCA9685...")
    i2c = busio.I2C(board.SCL, board.SDA)
    pca = PCA9685(i2c)
    pca.frequency = PCA_FREQ

    print(f"PCA9685 connected at {PCA_FREQ} Hz")
    stop_all_motors(pca)
    print("All motor channels stopped")

    print("Connecting to pigpio...")
    pi = pigpio.pi()

    if not pi.connected:
        print("ERROR: pigpio not connected")
        print("Run: sudo systemctl enable --now pigpiod")
        return

    encoders = [
        Encoder(pi, cfg["a"], cfg["b"], cfg["name"], cfg["invert"])
        for cfg in ENCODER_CONFIG
    ]

    print("Encoders initialized")
    print(f"Safety MAX_SPEED = {MAX_SPEED}%")
    print(f"Listening on port {PORT}")

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((HOST, PORT))
            server.listen(1)

            while True:
                print("\nWaiting for Pi 5 / laptop client...")
                conn, addr = server.accept()
                print(f"Connected by {addr}")

                buffer = ""
                last_cmd_time = time.time()

                conn.settimeout(0.1)

                with conn:
                    while True:
                        if time.time() - last_cmd_time > WATCHDOG_TIMEOUT:
                            stop_all_motors(pca)

                        try:
                            data = conn.recv(1024)

                        except socket.timeout:
                            continue

                        if not data:
                            print("Client disconnected")
                            stop_all_motors(pca)
                            break

                        buffer += data.decode("utf-8", errors="replace")

                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            line = line.strip()

                            if not line:
                                continue

                            try:
                                cmd = json.loads(line)
                                show_log = True

                                if "drive" in cmd:
                                    try:
                                        r_log, l_log = parse_drive(cmd["drive"])
                                        show_log = abs(r_log) > 0.1 or abs(l_log) > 0.1
                                    except Exception:
                                        show_log = True

                                if show_log:
                                    print("Received:", cmd)

                                reply = handle_command(cmd, pca, encoders)
                                last_cmd_time = time.time()

                            except Exception as e:
                                print("Command error:", e)
                                stop_all_motors(pca)

                                reply = {
                                    "status": "error",
                                    "error": str(e),
                                    "encoders": encoder_status(encoders)
                                }

                            conn.sendall((json.dumps(reply) + "\n").encode("utf-8"))

    except KeyboardInterrupt:
        print("\nKeyboard interrupt. Stopping motors...")

    finally:
        stop_all_motors(pca)

        for e in encoders:
            e.cancel()

        pi.stop()
        print("Shutdown complete. Motors stopped.")


if __name__ == "__main__":
    main()