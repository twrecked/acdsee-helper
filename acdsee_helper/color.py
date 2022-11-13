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