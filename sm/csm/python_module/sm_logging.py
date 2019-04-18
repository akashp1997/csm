import utils
import os
import sys

sm_program_name = ""
sm_program_name_temp = ""

sm_debug_write_flag = False
checked_for_xterm_color = False
xterm_color_available = False
sm_log_context = []

COLOR_ERROR = "\033[1;31m"
COLOR_RESET = "\033[0;0m"
COLOR_DEBUG = "\033[1;33m"

def sm_set_program_name(name):
    sm_program_name = my_basename_no_suffix(name)

def sm_debug_write(flag):
    sm_debug_write_flag = flag

def check_for_xterm_color():
    if checked_for_xterm_color:
        return
    checked_for_xterm_color = True

    term = os.environ.get("TERM", "unavailable")
    xterm_color_available = term=="xterm-color" or term=="xterm" or term=="rxvt"

def sm_write_context():
    sys.stderr.write("   "*len(sm_log_context))

def sm_debug(msg, *args):
    if not sm_debug_write_flag:
        return

    checked_for_xterm_color()

    if xterm_color_available:
        sys.stderr.write(COLOR_DEBUG)

    if sm_program_name:
        sys.stderr.write("%s: " % sm_program_name)

    sm_write_context()

    if not xterm_color_available:
        sys.stderr.write(":dbg: ", stderr)

    for arg in args:
        sys.stderr.write(str(arg)+" ")

    if xterm_color_available:
        sys.stderr.write(COLOR_RESET)

def sm_error(msg, *args):
    checked_for_xterm_color()
    if xterm_color_available :
        sys.stderr.write(COLOR_ERROR)
    if sm_program_name :
        sys.stderr.write("%s" % sm_program_name)

    sm_write_context()

    if not xterm_color_available:
        sys.stderr.write(":err: ")

    for arg in args:
        sys.stderr.write(str(arg)+" ")

    if xterm_color_available:
        sys.stderr.write(COLOR_RESET)

def sm_info(msg, *args):
    checked_for_xterm_color()
    if sm_program_name:
        sys.stderr.write("%s: " % sm_program_name)

    sm_write_context()

    if not xterm_color_available:
        sys.stderr.write(":inf: ")

    for arg in args:
        sys.stderr.write(str(arg) + " ")

def sm_log_push(cname):
    if sm_debug_write_flag:
        message = "  ___ %s \n" % cname
        sm_debug(message)

    sm_log_context.append(cname)


def sm_log_pop():
    if(len(sm_log_context)>0):
        sm_log_context.pop(-1)
