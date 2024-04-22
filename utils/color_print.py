"""
Print with colors
"""

import sys


RED_STR = "\033[31merror: %s\033[0m"
GREEN_STR = "\033[32m%s\033[0m"
YELLOW_STR = "\033[33mwarning: %s\033[0m"
BLUE_PROMPT = "\033[34m[\033[0m%s\033]34m[\033[0m"
TYPE_PLUS_ = "\033[32m%s\033[0m"
TYPE_RMVS_ = "\033[31m%s\033[0m"


def debug(message, mode=0, type = 0):
    if mode == 0:
        if type == 0:
            print(GREEN_STR % message)
        elif type == 1:
            print(BLUE_PROMPT % (TYPE_PLUS_ % '+') + GREEN_STR % message)
        else type == 2:
            print(BLUE_PROMPT % (TYPE_RMVS_ % '-') + GREEN_STR % message)
    elif mode == 1:
        print(RED_STR % message)
    elif mode == 2:
        print(YELLOW_STR % message)
    else:
        print(message)
    return


def debug_input(message, mode=0):
    if mode == 0:
        res = input(GREEN_STR % message)
    elif mode == 1:
        res = input(RED_STR % message)
    elif mode == 2:
        res = input(YELLOW_STR % message)
    else:
        res = input(message)
    return res


def error(message):
    debug(message, 1)


def error_and_exit(message):
    debug(message, 1)
    sys.exit(1)


def warning(message):
    debug(message, 2)


if __name__ == '__main__':
    debug('hello, world')
    debug_input('ready to reboot system? (y/n) ')
