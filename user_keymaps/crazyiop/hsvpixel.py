from math import sin, pi

try:
    from neopixel_write import neopixel_write
    import digitalio
except ImportError:

    def neopixel_write(pin, buf):
        print(f"sending {buf} on pin {pin}")

# builtin alias color name
# Inspired from https://github.com/dracula/dracula-theme
dracula = {
    "red": (0, 0.88, 0.35),
    "orange": (48, 0.85, 0.35),
    "yellow": (90, 0.81, 0.3),
    "green": (160, 0.88, 0.34),
    "cyan": (195, 0.81, 0.35),
    "purple": (270, 0.79, 0.34),
    "pink": (318, 0.83, 0.35),
    "white": (60, 0.03, 0.97),
    "black": (0, 0, 0),
}


def float_to_u8(value):
    return int(255 * value)


def hsv2rgb_rainbow(h, s=0.82, v=0.34):
    h = int(h) % 360
    quadrant, offset = divmod(h, 360 // 8)
    third = 1 / 3
    frac = offset * third / (360 // 8)

    if quadrant == 0:
        r, g, b = 1 - frac, frac, 0
    elif quadrant == 1:
        r, g, b = 1 - third, third + frac, 0
    elif quadrant == 2:
        r, g, b = 1 - third - 2 * frac, 2 * third + frac, 0
    elif quadrant == 3:
        r, g, b = 0, 1 - frac, frac
    elif quadrant == 4:
        r, g, b = 0, 1 - third - 2 * frac, third + 2 * frac
    elif quadrant == 5:
        r, g, b = frac, 0, 1 - frac
    elif quadrant == 6:
        r, g, b = third + frac, 0, 1 - third - frac
    elif quadrant == 7:
        r, g, b = 2 * third + frac, 0, 1 - 2 * third - frac

    # Normalize
    m = v * (1 - s)
    return (
        float_to_u8(r * (v - m) + m),
        float_to_u8(g * (v - m) + m),
        float_to_u8(b * (v - m) + m),
    )


class HSVPixel:
    def __init__(self, pin, n, pixel_order=(0,1,2), order='grb'):
        self.n = n
        self.order = order
        try:
            self.pin = digitalio.DigitalInOut(pin)
            self.pin.direction = digitalio.Direction.OUTPUT
        except NameError:
            self.pin = pin
        self.buffer = bytearray(n * 3)
        self.pixel_order = pixel_order

        self.S = 0.82
        self.V = 0.34

    def show(self):
        neopixel_write(self.pin, self.buffer)

    def __len__(self):
        return self.n

    def fill(self, value, skip=0):
        if value is None:
            value = 0, 0, 0
        for i in range(len(self)):
            if not i % (skip + 1):
                self[i] = value
            else:
                self[i] = None

    def to_rgb(self, value):
        if value is None:
            return (0, 0, 0)

        if isinstance(value, str):
            if value.lower() in dracula:
                h, s, v = dracula[value.lower()]
            else:
                raise ValueError("no color {} in {}".format(value, dracula))
        elif isinstance(value, int):
            # only h given
            h, s, v = value, self.S, self.V
        else:
            h, s, v = value

        return hsv2rgb_rainbow(h, s, v)

    def __setitem__(self, index, value):
        rgb = self.to_rgb(value)
        for i, col, letter in zip(self.pixel_order, rgb, 'rgb'):
            j = self.order.index(letter)
            self.buffer[3*index +j] = col

    def shift(self, n):
        offset = n * 3
        tmp = self.buffer[::]
        for i in range(self.n * 3):
            self.buffer[i] = tmp[(i + offset) % (self.n * 3)]

    def sinusoid(self, start, sigma=30, n=1):
        end = start + sigma
        start = start - sigma
        start, end = min(start, end), max(start, end)
        if end - start > 180:
            start, end = end, start + 360
        for i in range(len(self)):
            x = 1 + sin(2 * n * i * pi / len(self))
            self[i] = start + int((end - start) * x) // 2
