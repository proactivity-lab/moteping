"""packets.py: MotePing util."""
import sys

__author__ = "Raido Pahtma"
__license__ = "MIT"


print_colors = False


def has_colors():
    if sys.platform == 'win32':
        return False
    return True


def print_std(s):
    print(s)
    sys.stdout.flush()


def print_red(s):
    if print_colors:
        print("\033[91m{}\033[0m".format(s))
    else:
        print(s)
    sys.stdout.flush()


def print_green(s):
    if print_colors:
        print("\033[92m{}\033[0m".format(s))
    else:
        print(s)
    sys.stdout.flush()


def configure_colors(nocolor):
    global print_colors
    if nocolor is not None:  # Disable only if instructed, don't enable if disabled by environment
        print_colors = not nocolor
    else:
        print_colors = has_colors()
