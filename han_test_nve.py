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
from reader import parse_data, read_data_from_serial_port

# from hdlc import contains_full_message, extract_next_message

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

# python -m serial.tools.list_ports -v

# ----------------------------------------------------------------------------

CURRENT_VERSION = "v2.99 - 2023-03-28"
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


obis = {
    "1.0.1.7.0.255.": "Active power+(Q1+Q4)",
    "1.0.2.7.0.255.": "Active power-(Q1+Q4)",
    "1.0.3.7.0.255.": "Reactive power+ (Q1+Q2)",
    "1.0.4.7.0.255.": "Reactive power- (Q1+Q2)",
    "1.0.31.7.0.255.": "IL1",
    "1.0.51.7.0.255.": "IL2",
    "1.0.71.7.0.255.": "IL3",
    "1.0.32.7.0.255.": "UL1",
    "1.0.52.7.0.255.": "UL2",
    "1.0.72.7.0.255.": "UL3",
    "0.0.1.0.0.255.": "Clock",
    "1.0.1.8.0.255.": "A+cumul",
    "1.0.2.8.0.255.": "A-cumul",
    "1.0.3.8.0.255.": "R+cumul",
    "1.0.4.8.0.255.": "A-cumul",
    "1.1.0.2.129.255.": "OBIS list version id",
}


# def oct_2_obis(oct):
#     return obis.get(oct, "Unknown")


def printable(byte_data):
    outs = "%03d :" % 0
    for index in range(len(byte_data)):
        p = printable_byte(byte_data[index])

        s = "%2s" % (p)
        if (index + 1) % 30 == 0:
            s += "\n"
        outs += s
    return outs


def decode(byte_data):
    print("Decode....")
    outs = hdlc(byte_data)
    for ix in range(len(byte_data)):
        s = " %02x" % (byte_data[ix])
        if (ix + 1) % 20 == 0:
            s += "\n"
        outs += s
    return outs


# def print_byte_array(byte_data):
#     outs = "%03d :" % 0
#     for ix in range(len(byte_data)):
#         pcand = chr(byte_data[ix])
#         p = "/"
#         if pcand in string.printable:
#             p = pcand
#             if p == "\t":
#                 p = "TAB"
#             if p == "\n":
#                 p = "NLN"
#             if p == "\r":
#                 p = "CR"

#         s = " 0x%02x [%3d] (%7s)" % (byte_data[ix], byte_data[ix], p)
#         if (ix + 1) % 10 == 0:  # and ix < len(byte_data) - 10:
#             s += "\n%3d :" % ix
#         outs += s
#     return outs


# def read_bytes(given_bytes=0):
#     num_bytes = 0
#     while num_bytes <= given_bytes:
#         num_bytes = serial_port.in_waiting
#         # print "in_waiting: %d" % num_bytes
#         if num_bytes <= given_bytes:
#             time.sleep(1)
#     serialString = serial_port.read(num_bytes)
#     return bytearray(serialString)


def log_ringbuffer(buf):
    ringbuffer_log.write(get_now())
    ringbuffer_log.write("\n")
    ringbuffer_log.write(hexify(buf))
    rawlogfile_bytes.write(hexify(buf))
    ringbuffer_log.write("\n")


# def read_data_from_serial_port(serial_port):
#     ix = 0
#     ringbuffer = []

#     log_file.write(get_now())
#     log_file.write("\n")
#     log_file.write(f"Hafslund&Elvia HAN tester version: {CURRENT_VERSION}")
#     log_file.write("\n")
#     # ---------------
#     # The main loop
#     # waiting for and processing input from the serial port
#     # -----------------------------------------------------
#     while True:
#         ix += 1
#         s = "sleeping %d \r" % ix
#         print(s, end=" ")
#         time.sleep(1)
#         ix += 1
#         if serial_port.in_waiting > 0:
#             data = read_bytes(serial_port.in_waiting)
#             rawlogfile_binary.write(data)
#             ringbuffer.extend(data)
#             log_ringbuffer(ringbuffer)
#             parse_data(ringbuffer)


def read_data_from_file(i_file):
    """Read serial data from a text file."""
    lines_of_data = open(i_file).read()
    lines_of_data.replace(" ", "")
    lines_of_data.replace("\n", "")
    b = bytes.fromhex(lines_of_data)
    return bytearray(b)


if __name__ == "__main__":
    options = {}
    parse_command_line(options)
    input_file = options["file_name"]

    comport = options.get("comport")
    serial_port = get_comport(comport) if input_file is None or comport is None else None
    if input_file is not None:
        parse_data(read_data_from_file(input_file))
    elif serial_port is not None:
        read_data_from_serial_port(serial_port)
    else:
        print("No file given. No port available.\nquitting.\n")

    print("\n")
