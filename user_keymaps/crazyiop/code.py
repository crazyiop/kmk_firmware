import board
import usb_hid
from hsvpixel import HSVPixel
import random

from storage import getmount

from kmk.extensions.keymap_extras.keymap_bepo import BEPO
from kmk.extensions.status_indicator import Indicator
from kmk.extensions.media_keys import MediaKeys
from kmk.keys import make_mod_key, make_key
from kmk.kmk_keyboard import KMKKeyboard
from kmk.modules import Module
from kmk.modules.layers import Layers
from kmk.modules.modtap import ModTap
from kmk.modules.mouse_keys import MouseKeys
from kmk.modules.split import Split, SplitSide
from kmk.modules.tapdance import TapDance
from kmk.scanners import DiodeOrientation


keyboard = KMKKeyboard()
keyboard.debug_enabled = True

# Hardware
##########

side = SplitSide.RIGHT if str(getmount("/").label)[-1] == "R" else SplitSide.LEFT

# I completely mess my wiring that was suppossed to be identical...
if side == SplitSide.RIGHT:
    keyboard.col_pins = (board.MISO, board.CLK, board.A0, board.A1, board.A2, board.A3)
    keyboard.row_pins = (board.D3, board.D4, board.D5, board.D6, board.D7)
    keyboard.diode_orientation = DiodeOrientation.ROW2COL
else:
    keyboard.col_pins = (board.CLK, board.A0, board.A1, board.A2, board.A3)
    keyboard.row_pins = (board.D8, board.D7, board.D6, board.D5, board.D4, board.D3)
    keyboard.diode_orientation = DiodeOrientation.COL2ROW

split = Split(
    split_side=side,
    split_target_left=True,
    use_pio=True,
    data_pin=board.D12,
    data_pin2=board.D13,
    split_flip=False,
    uart_flip=True,
)

# fmt: off
keyboard.coord_mapping = [
    0, 5, 10, 15, 20, 25,  59, 58, 57, 56, 55, 54,
    1, 6, 11, 16, 21, 26,  53, 52, 51, 50, 49, 48,
    2, 7, 12, 17, 22, 27,  47, 46, 45, 44, 43, 42,
    3, 8, 13, 18, 23, 28,  41, 40, 39, 38, 37, 36,
          14, 19, 24, 29,  35, 34, 33, 32
]
# fmt: on


BASE = 0
LOWER = 1
RAISE = 2
NUMBER = 3
FN = 4
TOY = 5

# Modules
#########
class AltTab(Module):
    """
    Allow me to replicate the alt-tab(-tab)* without any alt key
    """

    def __init__(self):
        self.in_tab = False

    def after_matrix_scan(self, keyboard):
        if self.in_tab and LOWER not in keyboard.active_layers:
            keyboard.remove_key(BP.LALT)
            self.in_tab = False

    @staticmethod
    def on_press(
        key, keyboard, BP=None, coord_int=None, coord_raw=None, *args, **kwargs
    ):
        for module in keyboard.modules:
            if isinstance(module, AltTab):
                if not module.in_tab:
                    module.in_tab = True
                    keyboard.add_key(BP.LALT)
                keyboard.tap_key(BP.TAB)
                keyboard.hid_pending = True
                break
        return keyboard


tapdance = TapDance()
tapdance.tap_time = 200

keyboard.modules = [tapdance, split, Layers(), MouseKeys(), AltTab(), ModTap()]

# Extension
###########
pixel = HSVPixel(board.RX, 14)


class MyIndicator(Indicator):
    # off, h = 135, 0, 95, 46
    LAYERS_COLORS = [None, "cyan", "red", "green", "yellow"]
    CAPS_COLOR = (270, 0.0, 0.25)

    def __init__(self, pixel):
        super().__init__()
        self.np = pixel

    def update(self):
        side = str(getmount('/').label)[-1]
        layer = self.layers[0]
        caps = self.get_caps_lock()
        print('update led', side, layer, caps)

        if layer == TOY:
            return
        self.np.V = 0.34

        if side == 'L' and layer:
            # left always show layer color if any
            self.np.fill(self.LAYERS_COLORS[layer])
            self.np.show()
            return

        if caps:
            self.np.fill(self.CAPS_COLOR)
        else:
            self.np.fill(self.LAYERS_COLORS[layer])
        self.np.show()

    def on_powersave_enable(self, sandbox):
        self.np.fill(None)
        self.np.show()

    def on_powersave_disable(self, sandbox):
        self.update()


indicator = MyIndicator(pixel)
keyboard.extensions.append(indicator)
keyboard.extensions.append(MediaKeys())

# Layers/Keycode helper
#######################

BP = BEPO()

XXX = BP.NO
___ = BP.TRNS
VIM = BP.LCTL(BP.W)
TMUX = BP.LCTL(BP.B)
AA_TD = BP.TD(BP.A, BP.AGRAVE)
COMMA_TD = BP.TD(BP.COMMA, BP.SCLN)
PC_LOCK = BP.LALT(BP.LCTL(BP.L))
ALT_TAB = make_mod_key(
    code=None, names=tuple(), no_release=True, on_press=AltTab.on_press
)
MY_TAB = BP.LT(NUMBER, BP.TAB, prefer_hold=True)
MY_CAPS = BP.LT(FN, BP.CAPSLOCK, prefer_hold=True)

BP.ESC  # Nedded to cache key before MY_ESC is used (avoid pystack exhaustion)


def esc_remove_caps_press(key, keyboard, *args, **kwargs):
    keyboard.hid_pending = True
    if keyboard.extensions[0].get_caps_lock():
        keyboard.keys_pressed.add(BP.CAPSLOCK)
    keyboard.keys_pressed.add(BP.ESC)
    return keyboard


def esc_remove_caps_release(key, keyboard, *args, **kwargs):
    keyboard.hid_pending = True
    if keyboard.extensions[0].get_caps_lock():
        keyboard.keys_pressed.discard(BP.CAPSLOCK)
    keyboard.keys_pressed.discard(BP.ESC)
    return keyboard


def random_color(key, keyboard, *args, **kwargs):
    color = random.randint(0, 255)
    pixel.V = 0.7
    pixel.fill(color)
    pixel.show()


MY_ESC = make_key(on_press=esc_remove_caps_press, on_release=esc_remove_caps_release)
RND_COL = make_key(on_press=random_color)

# fmt: off
keyboard.keymap = [
    # 0, Base layer
    [
        BP.DOLLAR, BP.DQUOTE, BP.PERCENT,   MY_ESC,       XXX,    XXX,                               BP.AT,                   BP.PLUS,  BP.MINUS, BP.SLASH,     BP.ASTERISK, BP.EQUAL,
        MY_TAB,    BP.B,      BP.EACUTE,    BP.P,         BP.O,   BP.MT(BP.EGRAVE, BP.LSFT),         BP.MT(BP.DCIR, BP.RSFT), BP.V,     BP.D,     BP.L,         BP.J,        MY_CAPS,
        BP.W,      AA_TD,     BP.U,         BP.I,         BP.E,   COMMA_TD,                          BP.C,                    BP.T,     BP.S,     BP.R,         BP.N,        BP.M,
        BP.LCTRL,  BP.Z,      BP.Y,         BP.X,         BP.DOT, BP.K,                              BP.QUOTE,                BP.Q,     BP.G,     BP.H,         BP.F,        BP.RCTRL,

                              BP.MO(LOWER), BP.BACKSPACE, BP.DEL, BP.TO(TOY),                        XXX,                     BP.ENTER, BP.SPACE, BP.MO(RAISE),
    ],

    # 1, Lower, blue
    [
        ___,     ___,       ___,       ___,       ___,   ___,            ___,     ___,     ___,     ___,      ___,     ___,
        ALT_TAB, BP.AE,     BP.DACUTE, ___,       BP.OE, BP.DGRAVE,      ___,     TMUX,    BP.UP,   VIM,      ___,     ___,
        BP.VOLU, BP.AGRAVE, BP.UGRV,   BP.DTREMA, ___,   BP.TAPO,        BP.PGUP, BP.LEFT, BP.DOWN, BP.RIGHT, BP.PGDN, ___,
        BP.VOLD, BP.MPLY,   BP.MNXT,   ___,       ___,   ___,            ___,     BP.HOME, ___,     BP.END,   ___,     ___,

                            ___,       ___,       ___,   ___,            ___,     ___,     BP.UNDS, ___,
    ],

    # 2, Raise, red
    [
        ___,       ___,     BP.LESS, BP.GRTR, ___,     ___,          ___,     BP.MMNS, BP.PLMN, BP.DIV, BP.MUL, BP.NEQL,
        ___,       BP.PIPE, BP.LBRC, BP.RBRC, ___,     ___,          ___,     TMUX,    BP.UP,   PC_LOCK, ___,   ___,
        BP.MB_MMB, BP.AMPR, BP.LPRN, BP.RPRN, BP.EURO, ___,          BP.CCED, BP.LEFT, BP.DOWN, BP.RGHT, ___,   ___,
        ___,       BP.BSLS, BP.LCBR, BP.RCBR, BP.UNDS, BP.TILD,      ___,     ___,     BP.DGRK, ___,     ___,   ___,

                            ___,     ___,     ___,     ___,          ___,     ___,     ___,     ___,
    ],

    # 3, number, green
    [
        ___, ___, ___,     ___,     ___, ___,          ___, ___,   ___,   ___,   ___,   ___,
        ___, ___, ___,     ___,     ___, ___,          ___, BP.P7, BP.P8, BP.P9, BP.P0, BP.TAB,
        ___, ___, BP.LPRN, BP.RPRN, ___, BP.COMMA,     ___, BP.P4, BP.P5, BP.P6, ___,   ___,
        ___, ___, ___,     ___,     ___, ___,          ___, BP.P1, BP.P2, BP.P3, ___,   ___,
                  ___,     ___,     ___, ___,          ___, ___,   ___,   ___,
    ],

    # 4, fn
    [
        BP.F12, BP.F1, BP.F2, BP.F3, BP.F4, BP.F5,     BP.F6, BP.F7, BP.F8, BP.F9, BP.F10, BP.F11,
        ___,    ___,   ___,   ___,   ___,   ___,       ___,   ___,   ___,   ___,   ___,    ___,
        ___,    ___,   ___,   ___,   ___,   ___,       ___,   ___,   ___,   ___,   ___,    ___,
        ___,    ___,   ___,   ___,   ___,   ___,       ___,   ___,   ___,   ___,   ___,    ___,
                       ___,   ___,   ___,   ___,       ___,   ___,   ___,   ___,
    ],

    # 5, Toy. So that my children can 'work'.
    [
        BP.TO(0), RND_COL, RND_COL, RND_COL, RND_COL, RND_COL,
            RND_COL, RND_COL, RND_COL, RND_COL, RND_COL, RND_COL,
        RND_COL, RND_COL, RND_COL, RND_COL, RND_COL, RND_COL,
            RND_COL, RND_COL, RND_COL, RND_COL, RND_COL, RND_COL,
        RND_COL, RND_COL, RND_COL, RND_COL, RND_COL, RND_COL,
            RND_COL, RND_COL, RND_COL, RND_COL, RND_COL, RND_COL,
        RND_COL, RND_COL, RND_COL, RND_COL, RND_COL, RND_COL,
            RND_COL, RND_COL, RND_COL, RND_COL, RND_COL, RND_COL,

         RND_COL, RND_COL, RND_COL, RND_COL,
            RND_COL, RND_COL, RND_COL, RND_COL,
    ],
]
# fmt: on


if __name__ == "__main__":
    keyboard.go()
