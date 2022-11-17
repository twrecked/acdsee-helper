from colorama import Fore, Style

#
COLORS = {
    'red': Fore.RED,
    'green': Fore.GREEN,
    'yellow': Fore.YELLOW,
    'magenta': Fore.MAGENTA,
    'cyan': Fore.CYAN,
}
STYLES = {
    'bold': Style.BRIGHT,
}

no_color_ = False
verbose_ = 0


def color(msg, fg=None, style=None):
    if no_color_:
        return msg
    colors = ""
    if fg is not None and fg in COLORS:
        colors = COLORS[fg]
    if style is not None and style in STYLES:
        colors = colors + STYLES[style]
    return colors + msg + Style.RESET_ALL


def disable_color():
    global no_color_
    no_color_ = True


def enable_color():
    global no_color_
    no_color_ = False


def info(msg, fg='green', style='normal'):
    print(color(f'{msg}', fg=fg, style=style))


def warn(msg):
    print(color(f' {msg}', fg='yellow', style='bold'))


def error(msg):
    print(color(f' {msg}', fg='red', style='bold'))


def vprint(msg, fg='green', style='normal'):
    if verbose_ > 0:
        print(color(f' {msg}', fg=fg, style=style))


def vvprint(msg, fg='yellow', style='normal'):
    if verbose_ > 1:
        print(color(f' {msg}', fg=fg, style=style))


def set_verbosity(level):
    global verbose_
    verbose_ = level