import pigpio
import time


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
            if self.levB == 0:
                delta = 1
            else:
                delta = -1

        elif gpio == self.gpio_a and level == 0:
            if self.levB == 1:
                delta = 1
            else:
                delta = -1

        self.count += delta * self.invert

    def get_count(self):
        return self.count

    def cancel(self):
        self.cb_a.cancel()
        self.cb_b.cancel()


pi = pigpio.pi()

if not pi.connected:
    print("ERROR: pigpio not connected.")
    print("Run: sudo systemctl start pigpiod")
    exit(1)


# Corrected encoder mapping based on your wheel test
encoders = [
    Encoder(pi, 5, 6, "Right Back ", invert=-1),
    Encoder(pi, 24, 25, "Right Front", invert=-1),
    Encoder(pi, 22, 23, "Left Back  ", invert=1),
    Encoder(pi, 17, 27, "Left Front ", invert=1),
]


try:
    print("--- 4WD Encoder Feedback Monitor ---")
    print("Corrected encoder mapping applied.")
    print("Move each wheel forward by hand.")
    print("Expected: correct wheel name changes positive.")
    print("Press Ctrl+C to stop.\n")

    while True:
        status = " | ".join([f"{e.name}: {e.get_count():6d}" for e in encoders])
        print(f"\r{status}", end="", flush=True)
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\n\nTest Finished.")

finally:
    for e in encoders:
        e.cancel()

    pi.stop()