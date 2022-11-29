"""HAN port tester."""
import datetime
import os.path
import re
import string
import sys
import time

import serial
import serial.tools.list_ports as lp

# Revision history
# ---------- -------------         ------------------------------------------
# 2020-12-07 jaws         - v2    - Added rudimentary exception handling
# 2020-12-07 jaws         - v2.1  - Adding logging of ringbuffer
# 2020-12-07 jaws         - v2.11 - Fixed a bug in log_ringbuffer
# 2020-12-07 jaws         - v2.12 - Removed finally-clause which caused all log files to close.
# 2020-12-07 jaws         - v2.13 - added newline to logfile output
# 2022-11-15 jaws         - v2.14 - Fixing linting warnings while trying to add UL3 decoding output
# 2022-11-21 jaws         - v2.15 - Started working on offline/dry-run capabilities

# python -m serial.tools.list_ports -v

# ----------------------------------------------------------------------------

CURRENT_VERSION = "v2.15 - 2022-11-15"
print(f"Hafslund&Elvia HAN tester version: {CURRENT_VERSION}")


def parse_command_line(options):
    options["file_name"] = None
    for a in sys.argv:
        if a == "--help":
            print("===================================================")
            print(f"Hafslund&Elvia HAN tester version: {CURRENT_VERSION}")
            print("===================================================")
            print("--help")
            print("--version")
            print("--from-file=<file name>")
            exit(0)

        elif a == "--version":
            print(f"VERSION: {CURRENT_VERSION}")
            exit(0)
        elif a.startswith("--from-file="):
            fname = re.search(r"--from-file=(.*)", a).group(1)
            if os.path.exists(fname):
                print(f"File name is {fname}")
                options["file_name"] = fname
            else:
                print(f"No such file: {fname}")
                exit(0)
        elif a != sys.argv[0]:
            print(f"Unknown argument: {a}")
            exit(0)


# fmt: off
# example list 3 for 6525
list3_string_6525 = [0x7e, 0xa1, 0x77, 0x41, 0x08, 0x83, 0x13, 0x39, 0x1e, 0xe6, 0xe7, 0x00, 0x0f, 0x40, 0x00, 0x00,
                     0x00, 0x00, 0x01, 0x11, 0x02, 0x02, 0x09, 0x06, 0x01, 0x01, 0x00, 0x02, 0x81, 0xff, 0x0a, 0x0b,
                     0x41, 0x49, 0x44, 0x4f, 0x4e, 0x5f, 0x56, 0x30, 0x30, 0x30, 0x31, 0x02, 0x02, 0x09, 0x06, 0x00,
                     0x00, 0x60, 0x01, 0x00, 0xff, 0x0a, 0x10, 0x37, 0x33, 0x35, 0x39, 0x39, 0x39, 0x32, 0x39, 0x30,
                     0x38, 0x30, 0x35, 0x36, 0x30, 0x34, 0x38, 0x02, 0x02, 0x09, 0x06, 0x00, 0x00, 0x60, 0x01, 0x07,
                     0xff, 0x0a, 0x04, 0x36, 0x35, 0x32, 0x35, 0x02, 0x03, 0x09, 0x06, 0x01, 0x00, 0x01, 0x07, 0x00,
                     0xff, 0x06, 0x00, 0x00, 0x00, 0x0a, 0x02, 0x02, 0x0f, 0x00, 0x16, 0x1b, 0x02, 0x03, 0x09, 0x06,
                     0x01, 0x00, 0x02, 0x07, 0x00, 0xff, 0x06, 0x00, 0x00, 0x00, 0x00, 0x02, 0x02, 0x0f, 0x00, 0x16,
                     0x1b, 0x02, 0x03, 0x09, 0x06, 0x01, 0x00, 0x03, 0x07, 0x00, 0xff, 0x06, 0x00, 0x00, 0x00, 0x00,
                     0x02, 0x02, 0x0f, 0x00, 0x16, 0x1d, 0x02, 0x03, 0x09, 0x06, 0x01, 0x00, 0x04, 0x07, 0x00, 0xff,
                     0x06, 0x00, 0x00, 0x00, 0x00, 0x02, 0x02, 0x0f, 0x00, 0x16, 0x1d, 0x02, 0x03, 0x09, 0x06, 0x01,
                     0x00, 0x1f, 0x07, 0x00, 0xff, 0x10, 0x00, 0x00, 0x02, 0x02, 0x0f, 0xff, 0x16, 0x21, 0x02, 0x03,
                     0x09, 0x06, 0x01, 0x00, 0x47, 0x07, 0x00, 0xff, 0x10, 0x00, 0x00, 0x02, 0x02, 0x0f, 0xff, 0x16,
                     0x21, 0x02, 0x03, 0x09, 0x06, 0x01, 0x00, 0x20, 0x07, 0x00, 0xff, 0x12, 0x09, 0x07, 0x02, 0x02,
                     0x0f, 0xff, 0x16, 0x23, 0x02, 0x03, 0x09, 0x06, 0x01, 0x00, 0x34, 0x07, 0x00, 0xff, 0x12, 0x09,
                     0x13, 0x02, 0x02, 0x0f, 0xff, 0x16, 0x23, 0x02, 0x03, 0x09, 0x06, 0x01, 0x00, 0x48, 0x07, 0x00,
                     0xff, 0x12, 0x09, 0x03, 0x02, 0x02, 0x0f, 0xff, 0x16, 0x23, 0x02, 0x02, 0x09, 0x06, 0x00, 0x00,
                     0x01, 0x00, 0x00, 0xff, 0x09, 0x0c, 0x07, 0xe3, 0x02, 0x1a, 0x02, 0x0c, 0x00, 0x00, 0xff, 0x00,
                     0x00, 0x00, 0x02, 0x03, 0x09, 0x06, 0x01, 0x00, 0x01, 0x08, 0x00, 0xff, 0x06, 0x00, 0x00, 0x2e,
                     0x08, 0x02, 0x02, 0x0f, 0x01, 0x16, 0x1e, 0x02, 0x03, 0x09, 0x06, 0x01, 0x00, 0x02, 0x08, 0x00,
                     0xff, 0x06, 0x00, 0x00, 0x00, 0x00, 0x02, 0x02, 0x0f, 0x01, 0x16, 0x1e, 0x02, 0x03, 0x09, 0x06,
                     0x01, 0x00, 0x03, 0x08, 0x00, 0xff, 0x06, 0x00, 0x00, 0x00, 0x00, 0x02, 0x02, 0x0f, 0x01, 0x16,
                     0x20, 0x02, 0x03, 0x09, 0x06, 0x01, 0x00, 0x04, 0x08, 0x00, 0xff, 0x06, 0x00, 0x00, 0x18, 0x21,
                     0x02, 0x02, 0x0f, 0x01, 0x16, 0x20, 0x1b, 0x0f, 0x7e]

list3_string_6515 = [
    0x7e, 0xa1, 0x3e, 0x41, 0x08, 0x83, 0x13, 0x7f, 0x8e, 0xe6, 0xe7, 0x00, 0x0f, 0x40, 0x00, 0x00, 0x00, 0x00, 0x01, 0x0e
    , 0x02, 0x02, 0x09, 0x06, 0x01, 0x01, 0x00, 0x02, 0x81, 0xff, 0x0a, 0x0b, 0x41, 0x49, 0x44, 0x4f, 0x4e, 0x5f, 0x56, 0x30
    , 0x30, 0x30, 0x31, 0x02, 0x02, 0x09, 0x06, 0x00, 0x00, 0x60, 0x01, 0x00, 0xff, 0x0a, 0x10, 0x37, 0x33, 0x35, 0x39, 0x39
    , 0x39, 0x32, 0x38, 0x39, 0x38, 0x36, 0x30, 0x38, 0x30, 0x31, 0x32, 0x02, 0x02, 0x09, 0x06, 0x00, 0x00, 0x60, 0x01, 0x07
    , 0xff, 0x0a, 0x04, 0x36, 0x35, 0x31, 0x35, 0x02, 0x03, 0x09, 0x06, 0x01, 0x00, 0x01, 0x07, 0x00, 0xff, 0x06, 0x00, 0x00
    , 0x00, 0x06, 0x02, 0x02, 0x0f, 0x00, 0x16, 0x1b, 0x02, 0x03, 0x09, 0x06, 0x01, 0x00, 0x02, 0x07, 0x00, 0xff, 0x06, 0x00
    , 0x00, 0x00, 0x00, 0x02, 0x02, 0x0f, 0x00, 0x16, 0x1b, 0x02, 0x03, 0x09, 0x06, 0x01, 0x00, 0x03, 0x07, 0x00, 0xff, 0x06
    , 0x00, 0x00, 0x00, 0x00, 0x02, 0x02, 0x0f, 0x00, 0x16, 0x1d, 0x02, 0x03, 0x09, 0x06, 0x01, 0x00, 0x04, 0x07, 0x00, 0xff
    , 0x06, 0x00, 0x00, 0x00, 0x08, 0x02, 0x02, 0x0f, 0x00, 0x16, 0x1d, 0x02, 0x03, 0x09, 0x06, 0x01, 0x00, 0x1f, 0x07, 0x00
    , 0xff, 0x10, 0x00, 0x00, 0x02, 0x02, 0x0f, 0xff, 0x16, 0x21, 0x02, 0x03, 0x09, 0x06, 0x01, 0x00, 0x20, 0x07, 0x00, 0xff
    , 0x12, 0x09, 0x0f, 0x02, 0x02, 0x0f, 0xff, 0x16, 0x23, 0x02, 0x02, 0x09, 0x06, 0x00, 0x00, 0x01, 0x00, 0x00, 0xff, 0x09
    , 0x0c, 0x07, 0xe3, 0x02, 0x1a, 0x02, 0x0f, 0x00, 0x00, 0xff, 0x00, 0x00, 0x00, 0x02, 0x03, 0x09, 0x06, 0x01, 0x00, 0x01
    , 0x08, 0x00, 0xff, 0x06, 0x00, 0x00, 0x17, 0x1c, 0x02, 0x02, 0x0f, 0x01, 0x16, 0x1e, 0x02, 0x03, 0x09, 0x06, 0x01, 0x00
    , 0x02, 0x08, 0x00, 0xff, 0x06, 0x00, 0x00, 0x00, 0x00, 0x02, 0x02, 0x0f, 0x01, 0x16, 0x1e, 0x02, 0x03, 0x09, 0x06, 0x01
    , 0x00, 0x03, 0x08, 0x00, 0xff, 0x06, 0x00, 0x00, 0x00, 0x00, 0x02, 0x02, 0x0f, 0x01, 0x16, 0x20, 0x02, 0x03, 0x09, 0x06
    , 0x01, 0x00, 0x04, 0x08, 0x00, 0xff, 0x06, 0x00, 0x00, 0x1b, 0xf5, 0x02, 0x02, 0x0f, 0x01, 0x16, 0x20, 0xa1, 0x19, 0x7e
]
# fmt on

list2_file = open('list2.txt', 'a')
list3_file = open('list3.txt', 'a')
list1_file = open('list1.txt', 'a')
log_file = open('rawlog.txt', 'a')
ringbuffer_log = open('ringbuffer.txt', 'a')
rawlogfile_binary = open('rawlogfile_binary.txt', 'ab')
rawlogfile_bytes = open('rawlogfile_bytes', 'a')


obis = {
    '1.0.1.7.0.255.': 'Active power+(Q1+Q4)',
    '1.0.2.7.0.255.': 'Active power-(Q1+Q4)',
    '1.0.3.7.0.255.': 'Reactive power+ (Q1+Q2)',
    '1.0.4.7.0.255.': 'Reactive power- (Q1+Q2)',
    '1.0.31.7.0.255.': 'IL1',
    '1.0.51.7.0.255.': 'IL2',
    '1.0.71.7.0.255.': 'IL3',
    '1.0.32.7.0.255.': 'UL1',
    '1.0.52.7.0.255.': 'UL2',
    '1.0.72.7.0.255.': 'UL3',
    '0.0.1.0.0.255.': 'Clock',
    '1.0.1.8.0.255.': 'A+cumul',
    '1.0.2.8.0.255.': 'A-cumul',
    '1.0.3.8.0.255.': 'R+cumul',
    '1.0.4.8.0.255.': 'A-cumul',
     '1.1.0.2.129.255.': 'OBIS list version id'

}


def oct_2_obis(oct):
    return obis.get(oct, 'Unknown')


def get_now():
    return f'{[datetime.datetime.now().strftime("%a, %d %B %Y %H:%M:%S")]}'


def printable(byte_data):
    outs = "%03d :" % 0
    for ix in range(len(byte_data)):
        pcand = chr(byte_data[ix])
        p = ' '
        if pcand in string.printable:
            p = pcand
            if p == '\t':
                p = ' '
            if p == ' ':
                p = ' '
            if p == '\r':
                p = ' '

        s = "%2s" % (p)
        if (ix + 1) % 30 == 0:  # and ix < len(byte_data) - 10:
            s += "\n"
        outs += s
    return outs


def get_simple_print_byte_array(byte_data):
    outs = ''
    for ix in range(len(byte_data)):
        s = " %02x" % (byte_data[ix])
        if (ix + 1) % 20 == 0:  # and ix < len(byte_data) - 10:
            s += "\n"
        outs += s
    return outs


def simple_print_byte_array(byte_data):
    outs = get_simple_print_byte_array(byte_data)
    print(outs)
    return outs


def print_byte_array(byte_data):
    outs = "%03d :" % 0
    for ix in range(len(byte_data)):
        pcand = chr(byte_data[ix])
        p = '/'
        if pcand in string.printable:
            p = pcand
            if p == '\t':
                p = 'TAB'
            if p == '\n':
                p = 'NLN'
            if p == '\r':
                p = 'CR'

        s = " 0x%02x [%3d] (%7s)" % (byte_data[ix], byte_data[ix], p)
        if (ix + 1) % 10 == 0:  # and ix < len(byte_data) - 10:
            s += "\n%3d :" % ix
        outs += s
    return outs



def find_start(byte_data):
    """
    Remove everything from byte stream leading up to the first 0x7e
    :param byte_data:
    :return:
    """
    if len(byte_data) < 2:
        return False

    while len(byte_data) >= 2:
        if (byte_data[0] == 0x7e and byte_data[1] == 0x7e):
            # Throw away the first 7e. The second one will be the start of a message
            throwing = byte_data.pop(0)
            return True
        else:
            throwing = byte_data.pop(0)
            # print "Throwing: 0x%02x" % throwing

    return False


def contains_full_message(byte_data):
    """
    See if the byte_data contains a complete list from meter. 
    The lists start and end with 0x7e.

    Parameters
    ----------
    byte_data : _type_
        _description_

    Returns
    -------
    _type_
        _description_
    """
    try:
        retval = False
        local_ix = 0
        count_7es = 0
        # first_7e_ix = 0
        # second_7e_ix = 0
        while local_ix < len(byte_data):
            # print(f"{byte_data[local_ix]}, {hex(byte_data[local_ix])}")
            if byte_data[local_ix] == 0x7e:
                count_7es += 1
                if count_7es == 1:
                    if byte_data[local_ix + 1] == 0x7e:
                        # this was the border between an end and the start of the next message
                        local_ix += 1
                    # first_7e_ix = ix
                else:
                    count_7es += 1
                    # second_7e_ix = ix

            local_ix += 1
            if count_7es >= 2:
                retval = True
                break

        return retval
    except Exception:
        return False


def extract_next_message(byte_data):
    # print(f"byte_data:\n{byte_data}\n{byte_data.__class__}")
    retval = []
    if (byte_data[0] == 0x7e and byte_data[1] != 0x7e):
        print(".")
    else:
        find_start(byte_data)

    the_count = 0
    while the_count < 2:
        # print "the_count: %d" % the_count
        the_byte = byte_data.pop(0)
        # print "the byte: %02x" % the_byte
        if the_byte == 0x7e:
            the_count += 1

        retval.append(the_byte)

    print("Extracted message length: %d" % len(retval))

    return retval


def read_bytes(given_bytes=0):
    num_bytes = 0
    while num_bytes <= given_bytes:
        num_bytes = serial_port.in_waiting
        # print "in_waiting: %d" % num_bytes
        if num_bytes <= given_bytes:
            time.sleep(1)
    serialString = serial_port.read(num_bytes)
    return bytearray(serialString)


def get_bytes_as_string(ix, num_bytes, input):
    i = 0
    ret_string = ''
    while i < num_bytes:
        ret_string += f"{chr(input[ix + i])}"
        i += 1
    return ret_string


def append0x(str, ix, num_bytes, input):
    i = 0

    while i < num_bytes and (ix + 1 < len(input)):
        str += "%02x" % input[ix + i]
        i += 1
    str += " "
    return str


def parse_spec(spec, byte_data):
    """
    Use the provided spec to parse and display the data in byte_data.

    Parameters
    ----------
    spec : _type_
        _description_
    byte_data : _type_
        _description_

    Returns
    -------
    total_string: string
        The decoded string
    """
    current_ix = 0
    the_string = ''
    total_string = ''
    as_string = ''
    length_string = ''
    value = 0.0
    for s in spec:
        if s == '\n':
            total_string += "%-80s | %-45s - %f\n" % (the_string, as_string, value)
            the_string = ''
            as_string = ''
            value = 0.0
        elif s == 'r': # gives noof records
            s = 2
            the_string = append0x(the_string, current_ix, s, byte_data)
            current_ix += s
            as_string = " %d " % byte_data[current_ix - 1]
        elif s == 'h': # Hex data
            addr_field = byte_data[current_ix]
            length_field = byte_data[current_ix + 1]
            length_string = "addr: 0x%02x - length: 0x%02x/%d" % (addr_field, length_field, length_field)
            print(length_string)
            s = 2
            the_string = append0x(the_string, current_ix, s, byte_data)
            current_ix += s
        elif s == 'l': 
            # The data extracted here is a readable string, so
            # extract the length now
            length = byte_data[current_ix + 1]
            the_string = append0x(the_string, current_ix, 2, byte_data)
            current_ix += 2
            the_string = append0x(the_string, current_ix, length, byte_data)
            as_string = get_bytes_as_string(current_ix, length, byte_data)
            current_ix += length
        elif s == 'O': # There is an Obis code in this position
            s = 6
            the_string = append0x(the_string, current_ix, s, byte_data)
            obis_bytes = byte_data[current_ix:current_ix + s]
            if byte_data[current_ix + s] == 0x6:
                value_bytes = byte_data[current_ix + 7:current_ix + 7 + 4]
                x = 0
                for c in value_bytes:
                    x <<= 8
                    x |= c

                value = x

            if byte_data[current_ix + s] in [0x10, 0x12]:
                value_bytes = byte_data[current_ix + 7:current_ix + 7 + 2]
                x = 0
                for c in value_bytes:
                    x <<= 8
                    x |= c

                value = x / 10.0

            for b in obis_bytes:
                as_string += "%d." % b

            as_string += f" {oct_2_obis(as_string)}"
            current_ix += s
        elif s == 'R': # just output the rest of the message
            remainder = len(byte_data) - current_ix
            the_string = append0x(the_string, current_ix, remainder, byte_data)
        else:
            the_string = append0x(the_string, current_ix, s, byte_data)
            current_ix += s

    return total_string


def list3(byte_data):
    print("list3")
    print("lenght: %d" % (len(byte_data)))
    print(get_now())
    print(byte_data)
    print("===============================================\n============================\n==================")

    # fmt: off
    spec = [
        1, 'h', 1, 2, 1, 2, 3, '\n',
        1, 4, 1, '\n',
        'r', '\n',
        2, 2, 6, 'l', '\n',  # The length is stored here, at 'l'
        2, 2, 6, 'l', '\n',  # The length is stored here
        2, 2, 6, 'l', '\n',  # The length is stored here
        2, 2, 'O', 1, 4, 2, 2, 2, '\n',
        2, 2, 'O', 1, 4, 2, 2, 2, '\n',
        2, 2, 'O', 1, 4, 2, 2, 2, '\n',
        2, 2, 'O', 1, 4, 2, 2, 2, '\n',

        2, 2, 'O', 1, 2, 2, 2, 2, '\n',
        2, 2, 'O', 1, 2, 2, 2, 2, '\n',

        2, 2, 'O', 1, 13, '\n',
        2, 2, 'O', 1, 4, 2, 2, 2, '\n',
        2, 2, 'O', 1, 4, 2, 2, 2, '\n',
        2, 2, 'O', 1, 4, 2, 2, 2, '\n',
        2, 2, 'O', 1, 4, 2, 2, 2, '\n',
        'R', '\n'  # output the rest....
    ]
    # fmt: on
    if len(byte_data) > 350:
        # fmt: off
        spec = [
            1, 'h', 1, 2, 1, 2, 3, '\n',
            1, 4, 1, '\n',
            'r', '\n',
            2, 2, 6, 'l', '\n',  # The length is stored here, at 'l'
            2, 2, 6, 'l', '\n',  # The length is stored here
            2, 2, 6, 'l', '\n',  # The length is stored here
            2, 2, 'O', 1, 4, 2, 2, 2, '\n',
            2, 2, 'O', 1, 4, 2, 2, 2, '\n',
            2, 2, 'O', 1, 4, 2, 2, 2, '\n',
            2, 2, 'O', 1, 4, 2, 2, 2, '\n',

            2, 2, 'O', 1, 2, 2, 2, 2, '\n',
            2, 2, 'O', 1, 2, 2, 2, 2, '\n',
            2, 2, 'O', 1, 2, 2, 2, 2, '\n',
            2, 2, 'O', 1, 2, 2, 2, 2, '\n',
            2, 2, 'O', 1, 2, 2, 2, 2, '\n',

            2, 2, 'O', 1, 13, '\n',
            2, 2, 'O', 1, 4, 2, 2, 2, '\n',
            2, 2, 'O', 1, 4, 2, 2, 2, '\n',
            2, 2, 'O', 1, 4, 2, 2, 2, '\n',
            2, 2, 'O', 1, 4, 2, 2, 2, '\n',
            'R', '\n'  # output the rest....
        ]
        # fmt: on
    total_string = parse_spec(spec, byte_data)
    list3_file.write(get_now())
    list3_file.write(total_string)
    print(total_string)
    return total_string


def list2(byte_data):
    print(get_now())
    print("====\nLIST 2\n====")

    if len(byte_data) > 280:
        # Aidon's 6560 also needs UL3, typical length of message could be 288
        # fmt: off
        spec = [
            1, 'h', 1, 2, 1, 2, 3, '\n',
            1, 4, 1, '\n',
            'r', '\n',
            2, 2, 6, 'l', '\n',  # The length is stored here, at 'l'
            2, 2, 6, 'l', '\n',  # The length is stored here
            2, 2, 6, 'l', '\n',  # The length is stored here
            2, 2, 'O', 1, 4, 2, 2, 2, '\n',
            2, 2, 'O', 1, 4, 2, 2, 2, '\n',
            2, 2, 'O', 1, 4, 2, 2, 2, '\n',
            2, 2, 'O', 1, 4, 2, 2, 2, '\n',
            2, 2, 'O', 1, 2, 2, 2, 2, '\n',
            2, 2, 'O', 1, 2, 2, 2, 2, '\n',
            2, 2, 'O', 1, 2, 2, 2, 2, '\n',
            2, 2, 'O', 1, 2, 2, 2, 2, '\n',
            2, 2, 'O', 1, 2, 2, 2, 2, '\n',
            2, 2, 'O', 1, 2, 2, 2, 2, '\n',
            'R', '\n'  # output the rest....
        ]
        # fmt: on
    elif len(byte_data) > 220:
        spec = [
        # fmt: off
            1, 'h', 1, 2, 1, 2, 3, '\n',
            1, 4, 1, '\n',
            'r', '\n',
            2, 2, 6, 'l', '\n',  # The length is stored here, at 'l'
            2, 2, 6, 'l', '\n',  # The length is stored here
            2, 2, 6, 'l', '\n',  # The length is stored here
            2, 2, 'O', 1, 4, 2, 2, 2, '\n',
            2, 2, 'O', 1, 4, 2, 2, 2, '\n',
            2, 2, 'O', 1, 4, 2, 2, 2, '\n',
            2, 2, 'O', 1, 4, 2, 2, 2, '\n',
            2, 2, 'O', 1, 2, 2, 2, 2, '\n',
            2, 2, 'O', 1, 2, 2, 2, 2, '\n',
            2, 2, 'O', 1, 2, 2, 2, 2, '\n',
            2, 2, 'O', 1, 2, 2, 2, 2, '\n',
            2, 2, 'O', 1, 2, 2, 2, 2, '\n',
            'R', '\n'  # output the rest....
        ]
        # fmt: on
    else:
        # fmt: off
        spec = [
                1, 'h', 1, 2, 1, 2, 3, '\n',
                1, 4, 1, '\n',
                'r', '\n',
                2, 2, 6, 'l', '\n',  # The length is stored here, at 'l'
                2, 2, 6, 'l', '\n',  # The length is stored here
                2, 2, 6, 'l', '\n',  # The length is stored here
                2, 2, 'O', 1, 4, 2, 2, 2, '\n',
                2, 2, 'O', 1, 4, 2, 2, 2, '\n',
                2, 2, 'O', 1, 4, 2, 2, 2, '\n',
                2, 2, 'O', 1, 4, 2, 2, 2, '\n',
                2, 2, 'O', 1, 2, 2, 2, 2, '\n',
                2, 2, 'O', 1, 2, 2, 2, 2, '\n',
                'R', '\n'  # output the rest....
            ]
        # fmt: on

    total_string = parse_spec(spec, byte_data)
    list2_file.write(get_now())
    list2_file.write(total_string)
    print(total_string)
    return total_string


def list1(byte_data):
    print('---------')
    print(get_now())
    # fmt: off
    spec = [
        1, 'h', 1, 2, 1, 2, 3, '\n',
        1, 4, 1, '\n',
        'r', '\n',
        2, 2, 'O', 1, 4, 2, 2, 2, '\n',
        3, '\n',
        1, '\n'
    ]
    # fmt: off
    the_string = parse_spec(spec, byte_data)
    list1_file.write(get_now())
    list1_file.write(the_string)
    print(the_string)
    return the_string


def log_ringbuffer(buf):
    ringbuffer_log.write(get_now())
    ringbuffer_log.write("\n")
    ringbuffer_log.write(get_simple_print_byte_array(buf))
    rawlogfile_bytes.write(get_simple_print_byte_array(buf))
    ringbuffer_log.write("\n")


def get_comport():
    comport = 'No com port found'
    for sp in lp.comports():
        if sp.description.startswith('USB'):
            comport = sp.device
            break

    print(f"comport: {comport}")
    try:
        serial_port = serial.Serial(comport, 2400, timeout=2, parity=serial.PARITY_EVEN)
        print("Serial port created:")
        print(serial_port)

        serial_port.reset_input_buffer()
        # serialString = ""
    except Exception:

        print("Fant ingen com port.\nAvslutter.\n\n Ha det bra.")
        for sp in lp.comports():
            print(f"{sp} - {sp.description}")
        exit(0)

    return serial_port


def parse_data(ringbuffer):
    try:
        while contains_full_message(ringbuffer):
            next_message = extract_next_message(ringbuffer)

            raw_data = simple_print_byte_array(next_message)
            this_list = ''
            if len(next_message) > 300:
                this_list = list3(next_message)
            elif len(next_message) > 100:
                this_list = list2(next_message)
            elif len(next_message) > 40:
                this_list = list1(next_message)

            log_file.write(get_now())
            log_file.write(raw_data)
            log_file.write(this_list)
    except Exception as inst:
        print(inst)
        print('-----')
        print(ringbuffer)
        log_file.write("Exception in main while loop")
        log_file.write(type(inst))  # type: ignore
        log_file.write(inst.args)   # type: ignore
        log_file.write(str(inst))   # type: ignore


def read_data_from_serial_port(serial_port):
    ix = 0
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
        ix += 1
        s = "sleeping %d \r" % ix
        print(s, end=' ')
        time.sleep(1)
        ix += 1
        if serial_port.in_waiting > 0:
            data = read_bytes(serial_port.in_waiting)
            rawlogfile_binary.write(data)
            ringbuffer.extend(data)
            log_ringbuffer(ringbuffer)
            parse_data(ringbuffer)



def read_data_from_file(input_file):
    """Read serial data from a text file."""
    lines_of_data = open(input_file).read()
    lines_of_data.replace(' ','')
    lines_of_data.replace('\n','')
    b = bytes.fromhex(lines_of_data)
    bb = bytearray(b)
    return bb


if __name__ == '__main__':
    options = {}
    parse_command_line(options)
    input_file = options['file_name']

    serial_port = get_comport() if input_file is None else None
    if input_file is not None:
        parse_data(read_data_from_file(input_file))
    elif serial_port is not None:
        read_data_from_serial_port(serial_port)
    else:
        print("No file given. No port available.\nquitting.\n")

    print("\n")
