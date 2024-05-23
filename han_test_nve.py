"""HAN port tester."""
# pylint: disable=line-too-long
# pylint: disable=unspecified-encoding
# pylint: disable=consider-using-enumerate, missing-docstring, consider-using-f-string
import os.path
import re
import sys

from comport import get_comport
from han_utils import get_now, hexify, printable_byte
from hdlc import hdlc
from reader import parse_data, read_data_from_file, read_data_from_serial_port

# Revision history
# ---------- -------------         ------------------------------------------
# 2020-12-07 jaws         - v2    - Added rudimentary exception handling
# 2020-12-07 jaws         - v2.1  - Adding logging of ringbuffer
# 2020-12-07 jaws         - v2.11 - Fixed a bug in log_ringbuffer
# 2020-12-07 jaws         - v2.12 - Removed finally-clause which caused all log files to close.
# 2020-12-07 jaws         - v2.13 - added newline to logfile output
# 2022-11-15 jaws         - v2.14 - Fixing linting warnings while trying to add UL3 decoding output
# 2022-11-21 jaws         - v2.15 - Started working on offline/dry-run capabilities
# 2022-11-29 jaws         - v2.16 - Started working on added readability output
# 2023-03-28 jaws         - v2.99 - Started working on added major restructuring
# 2023-05-04 jaws         - v2.99 - Almost working

# python -m serial.tools.list_ports -v

# ----------------------------------------------------------------------------

CURRENT_VERSION = "v4.00 - 2024-05-23"
print(f"Elvia HAN tester version: {CURRENT_VERSION}")


def parse_command_line(l_options):
    l_options["file_name"] = None
    for argument in sys.argv:
        if argument == "--help":
            _print_help()
        elif argument == "--version":
            print(f"VERSION: {CURRENT_VERSION}")
            exit(0)
        elif argument.startswith("--from-file="):
            fname = re.search(r"--from-file=(.*)", argument)[1]
            if os.path.exists(fname):
                print(f"File name is {fname}")
                l_options["file_name"] = fname
            else:
                print(f"No such file: {fname}")
                exit(0)
        elif argument.startswith("--comport="):
            portname = re.search(r"--comport=(.*)", argument)[1]
            if os.path.exists(portname):
                print(f"Using comport {portname}")
                l_options["comport"] = portname
        elif argument != sys.argv[0]:
            print(f"Unknown argument: {argument}")
            exit(0)


def _print_help():
    print("===================================================")
    print(f"Hafslund&Elvia HAN tester version: {CURRENT_VERSION}")
    print("===================================================")
    print("--help")
    print("--version")
    print("--comport=COMPORT")
    print("--from-file=FILE-NAME")
    exit(0)


list2_file = open("list2.txt", "a")
list3_file = open("list3.txt", "a")
list1_file = open("list1.txt", "a")
log_file = open("rawlog.txt", "a")
ringbuffer_log = open("ringbuffer.txt", "a")
rawlogfile_binary = open("rawlogfile_binary.txt", "ab")
rawlogfile_bytes = open("rawlogfile_bytes", "a")


def printable(byte_data):
    outs = "%03d :" % 0
    for index in range(len(byte_data)):
        p = printable_byte(byte_data[index])

        s = "%2s" % (p)
        if (index + 1) % 30 == 0:
            s += "\n"
        outs += s
    return outs


if __name__ == "__main__":
    options = {}
    parse_command_line(options)
    input_file = options["file_name"]
    com_port = ''
    comport_path = options.get("comport")
    print(f"INPUT file: {input_file}")

    if input_file is None:
        com_port = get_comport(comport_path) if input_file is None or comport_path is None else None

    if input_file is not None:
        parse_data(read_data_from_file(input_file))
    elif com_port is not None:
        read_data_from_serial_port(com_port)
    else:
        print("No file given. No port available.\nquitting.\n")

    print("\n")
