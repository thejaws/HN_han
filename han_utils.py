# pylint: disable=consider-using-enumerate, missing-docstring, consider-using-f-string
import datetime
import string
import sys
from enum import Enum


class LogLevel(Enum):
    DEBUG = 3
    INFO = 6
    WARNING = 80
    ERROR = 90
    CRITICAL = 99
    EXCEPTION = 101


def logit(msg, lvl=LogLevel.DEBUG):
    if lvl.value > LogLevel.INFO.value:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")
        print(f"{lvl.name} {now}  ==:  {msg}")
        sys.stdout.flush()


def get_now():
    return f'{[datetime.datetime.now().strftime("%a, %d %B %Y %H:%M:%S")]}'


def simple_print_byte_array(byte_data):
    outs = hexify(byte_data)
    readable_string = ""
    for index, string_part in enumerate(byte_data, start=1):
        if index % 20 == 0:
            readable_string += "\n"
        readable_string += "%-3s" % printable_byte(string_part)

    return outs


def printable_byte(one_byte):
    pcand = chr(one_byte)
    return_printable = " . "
    if pcand in string.printable:
        return_printable = pcand
        if return_printable in {"\t", " ", "\r", "\n", chr(0x0b)}:
            return_printable = " "
    return return_printable


def hexify(byte_data, breakit=False):
    hex_string = ""
    for index in range(len(byte_data)):
        byte_as_hex = " %02x" % (byte_data[index])
        if breakit and (index + 1) % 20 == 0:
            byte_as_hex += "\n"
        hex_string += byte_as_hex
    return hex_string


def bytes_printable(byte_data, breakit=False):
    printable_string = ""
    for index, the_byte in enumerate(byte_data, start=1):
        if breakit and index % 20 == 0:
            printable_string += "\n"
        printable_string += "%-3s" % printable_byte(the_byte)
    return printable_string


def find_start(byte_data):
    """
    Remove everything from byte stream leading up to the first 0x7e.
    :param byte_data:
    :return:
    """
    print("find start")
    if len(byte_data) < 2:
        return False

    while len(byte_data) >= 2:
        if byte_data[0] == 0x7E and byte_data[1] == 0x7E:
            # Throw away the first 7e. The second one will be the start of a message
            throwing = byte_data.pop(0)
            print(f"Discarding: {throwing}")
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
        while local_ix < len(byte_data):
            if byte_data[local_ix] == 0x7E:
                count_7es += 1
                if count_7es == 1:
                    if byte_data[local_ix + 1] == 0x7E:
                        # this was the border between an end and the start of the next message
                        local_ix += 1
                else:
                    count_7es += 1

            local_ix += 1
            if count_7es >= 2:
                retval = True
                break

        return retval
    except Exception:
        return False


def which_list(this_list):
    if len(this_list) > 300:
        return "List 3"
    elif len(this_list) > 100:
        return "List 2"
    elif len(this_list) > 40:
        return "List 1"
