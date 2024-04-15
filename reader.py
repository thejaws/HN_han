"""HAN port tester."""
# pylint: disable=consider-using-enumerate, missing-docstring, consider-using-f-string
# pylint: disable=unspecified-encoding
# import serial
# import serial.tools.list_ports as lp
import datetime
import os.path
import re
import string
import sys
import time

from comport import get_comport
from han_utils import LogLevel, hexify, logit, simple_print_byte_array
from hdlc import (after_hdlc, contains_full_message, extract_next_message,
                  hdlc, the_payload)

CURRENT_VERSION = "v2.16 - 2022-11-29"
print(f"Hafslund&Elvia HAN tester version: {CURRENT_VERSION}")


list2_file = open("list2.txt", "a")
list3_file = open("list3.txt", "a")
list1_file = open("list1.txt", "a")
log_file = open("rawlog.txt", "a")
ringbuffer_log = open("ringbuffer.txt", "a")
rawlogfile_binary = open("rawlogfile_binary.txt", "ab")
rawlogfile_bytes = open("rawlogfile_bytes", "a")


def parse_command_line(options):
    options["file_name"] = None
    for a in sys.argv:
        if a == "--help":
            _print_help()
        elif a == "--version":
            print(f"VERSION: {CURRENT_VERSION}")
            exit(0)
        elif a.startswith("--from-file="):
            fname = re.search(r"--from-file=(.*)", a)[1]
            if os.path.exists(fname):
                print(f"File name is {fname}")
                options["file_name"] = fname
            else:
                print(f"No such file: {fname}")
                exit(0)
        elif a != sys.argv[0]:
            print(f"Unknown argument: {a}")
            exit(0)


def get_now():
    return f'{[datetime.datetime.now().strftime("%a, %d %B %Y %H:%M:%S")]}'


def printable_byte(one_byte):
    pcand = chr(one_byte)
    return_printable = " . "
    if pcand in string.printable:
        return_printable = pcand
        if return_printable == "\t":
            return_printable = " "
        if return_printable == " ":
            return_printable = " "
        if return_printable == "\r":
            return_printable = " "
    return return_printable


def printable(byte_data):
    outs = "%03d :" % 0
    for ix in range(len(byte_data)):
        p = printable_byte(byte_data[ix])

        s = "%2s" % (p)
        if (ix + 1) % 30 == 0:
            s += "\n"
        outs += s
    return outs


def read_bytes(com_port, given_bytes=0):
    num_bytes = 0
    while num_bytes <= given_bytes:
        num_bytes = com_port.in_waiting
        # print "in_waiting: %d" % num_bytes
        if num_bytes <= given_bytes:
            time.sleep(1)
    serial_string = com_port.read(num_bytes)
    # jaws
    rawlogfile_binary.write(serial_string)
    return bytearray(serial_string)


def log_ringbuffer(buf):
    ringbuffer_log.write(get_now())
    ringbuffer_log.write("\n")
    ringbuffer_log.write(hexify(buf))
    rawlogfile_bytes.write(hexify(buf))
    ringbuffer_log.write("\n")
    # rawlogfile_binary.write(bytes(buf))


def parse_data(ringbuffer):
    outs2 = ""
    while contains_full_message(ringbuffer):
        next_message = extract_next_message(ringbuffer)
        logit(f"{hexify(next_message)}", LogLevel.WARNING)
        raw_data = simple_print_byte_array(next_message)
        decode_this_message = next_message.copy()
        outs2 = hdlc(decode_this_message)
        outs2 += after_hdlc(decode_this_message)
        outs2 += the_payload(decode_this_message)
        log_ringbuffer(ringbuffer)


def read_data_from_file(i_file):
    """Read serial data from a text file."""
    data = None
    try:
        lines_of_data = open(i_file).read()
        lines_of_data.replace(" ", "")
        lines_of_data.replace("\n", "")
        data = bytes.fromhex(lines_of_data)
    except UnicodeDecodeError as ude:
        # maybe file is binary
        data = open(i_file, 'rb').read()

    byte_data = bytearray(data)
    return byte_data


def read_data_from_serial_port(com_port):
    ringbuffer = []

    log_file.write(get_now())
    log_file.write("\n")
    log_file.write(f"Hafslund&Elvia HAN tester version: {CURRENT_VERSION}")
    log_file.write("\n")

    # ---------------
    # The main loop
    # waiting for and processing input from the serial port
    # -----------------------------------------------------
    while True:
        time.sleep(1)
        if com_port.in_waiting > 0:
            try:
                data = read_bytes(com_port, com_port.in_waiting)
                ringbuffer.extend(data)
                parse_data(ringbuffer)
            except IndexError as ix_e:
                print(f"{ix_e}")


if __name__ == "__main__":
    options = {}
    parse_command_line(options)
    input_file = options["file_name"]

    serial_port = get_comport() if input_file is None else None
    if serial_port is not None:
        read_data_from_serial_port(serial_port)
    else:
        print("No file given. No port available.\nquitting.\n")

    print("\n")
