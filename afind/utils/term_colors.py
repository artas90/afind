
class TermColors(object):
    esc = b'\033['
    m = b'm'

    black, red, green, yellow, blue, magenta, cyan, white = 0, 1, 2, 3, 4, 5, 6, 7

    _fg, _bg, _bright, = 30, 40, +60
    _bold, _underline = 1, 4

    RESET = esc + b'0' + m

    @classmethod
    def make_flags(cls, fg=None, bg=None, fg_light=False, bg_light=False, bold=False, underline=False):
        flags = [
            (cls._bold     if bold             else 0) + (cls._underline if underline else 0),
            (cls._fg + fg  if (fg is not None) else 0) + (cls._bright    if fg_light  else 0),
            (cls._bg + bg  if (bg is not None) else 0) + (cls._bright    if bg_light  else 0),
        ]
        flags = b';'.join(bytes(f) for f in flags if f)
        return cls.esc + flags + cls.m
