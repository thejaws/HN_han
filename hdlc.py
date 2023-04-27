# pylint: disable=consider-using-enumerate, missing-docstring, consider-using-f-string
import contextlib
import traceback
from enum import Enum
from typing import Tuple

from han_utils import bytes_printable, hexify


class DataType(Enum):
    NULL_DATA = 0
    BOOLEAN = 3
    BIT_STRING = 4
    DOUBLE_LONG = 5
    DOUBLE_LONG_UNSIGNED = 6
    OCTET_STRING = 9
    VISIBLE_STRING = 10
    UTF8_STRING = 12
    INTEGER = 15
    LONG = 16
    UNSIGNED = 17
    LONG_UNSIGNED = 18
    LONG64 = 20
    LONG64_UNSIGNED = 21  # 0x15
    ENUM = 22  # ...........0x16
    DATE_TIME = 25
    DATE = 26

    # complex types ----
    ARRAY = 1
    STRUCTURE = 2
    OOMPACT_ARRAY = 19

    # default value
    UNKNOWN = 666


class PhysicalUnits(Enum):
    POWER = 27
    VA = 28
    VAR = 29
    ACTIVE_ENERGY = 30
    VARH = 32
    AMPERE = 33
    VOLTAGE = 35


class OneList:
    def __init__(self):
        self.records = []

    def add_row(self, row):
        self.records.append(row)

    def __str__(self) -> str:
        retval = ""
        for s in self.records:
            retval += f"\n{s}"
        return retval


class OneRecord:
    def __init__(self):
        self.hex = ''
        self.printable = ''
        self.decoded = ''

    def add_data(self, hex_string, ascii_string, value):
        self.hex += f"    {hex_string}"
        self.printable += f"    {ascii_string}"
        self.decoded += f" {value} "

    def __str__(self) -> str:
        return f"{self.hex}   {self.printable}   {self.decoded}"


def whatsit(data) -> Tuple[DataType, int]:
    print(f"whatsit, data: {hexify(data)}")
    noof_elements = 0
    complex_data_type = DataType.UNKNOWN
    try:
        complex_data_type = DataType(data[0])

        if complex_data_type in [DataType.DOUBLE_LONG, DataType.DOUBLE_LONG_UNSIGNED]:
            noof_elements = 4
        elif complex_data_type in [DataType.INTEGER, DataType.UNSIGNED]:
            noof_elements = 1
        elif complex_data_type in [DataType.LONG]:
            noof_elements = 2
        else:
            print(f"Whatsit else....: {complex_data_type.name}")
            noof_elements = data[1]
    except ValueError as value_error:
        print(f"GUESSING that it is not a known data type:\n{value_error}")
        print("XXX\n\nProbably end of List?")

    return complex_data_type, noof_elements


def the_payload(byte_data):
    """
    Handle the payload.

    "011b"
        01 = Liste
        1b = Antall elementer i lista. I dette tilfellet 27
    "0202 0906 0000010000ff 090c 07e30c1001073b28ff8000ff"
        02 = Struct
        02 = Antall elementer i Structen. I dette tilfellet 2
        09 = octet-string
        06 = Strenglengde. I dette tilfellet 6

        0000010000ff = strengen
        09 = octet-string
        0c = Strenglengde. I dette tilfellet 12

        07e30c1001073b28ff8000ff = strengen

    "0203 0906 0100010700ff 06 00000462 0202 0f00 161b"
        02 = Struct
        03 = Antall elementer i Structen. I dette tilfellet 3
        09 = octet-string
        06 = Strenglengde. I dette tilfellet 6

        0100010700ff = strengen
        06 = double-long-unsigned

        00000462 = verdien

        02 = Struct. NB! Struct i Struct! NNB! Dette er scaler_unit!!
        02 = Antall elementer i Structen. I dette tilfellet 2

        0f = integer
        00 = scaler
        16 = enum
        1b = unit. I dette tilfellet W - Active Power


    Parameters
    ----------
    byte_data : _type_
        _description_

    Returns
    -------
    _type_
        _description_
    """
    print(">>> the_payload()")
    retval = "Xxxx>"
    what, noof_records = whatsit(byte_data)
    print(f"What: {what} - Noof Records: {noof_records}")
    print(f"{hexify(byte_data[:2])}")

    retval += hexify(byte_data[:2])
    retval += "\n"
    retval += "Payl>"

    # strip_type_length(byte_data)
    del byte_data[:2]

    # Example of list 1
    # 7e a0 2a 41 08 83 13 04 13 e6 e7 00 0f 40 00 00 00 00
    # 01 01 <== List of 1 records
    # struct of 3 elems.
    #            | first elem     |
    #                                  | second elem is double long unsigned
    #                                                 | third elem is struct of two elems
    #                                                        | integer + scaler
    #                                                             | unit 1b which is Active power
    #  0203 0906 01 00 01 07 00 ff     06 00 00 00 00 02 02 0f 00 16 1b
    # ae 27 7e

    # Example of List 2
    # 7e a0 d2 41 08 83 13 82 d6 e6 e7 00
    # 0f 40 00 00 00 00
    # 01 09  <=== 09 should be noo records.
    #  0202 0906  01 01 00 02 81 ff     0a0b 41 49 44 4f 4e 5f 56 30 30 30 31
    #  0202 0906  00 00 60 01 00 ff     |0a10 37 33 35 39 39 39 32 39 30 30 32 36 32 31 34 30|
    #  0202 0906  00 00 60 01 07 ff     |0a04 36 35 31 35|
    #  0203 0906  01 00 01 07 00 ff     |06 - 00000000 | 0202 0f 00 16 1b|
    #   02 03 09 06 01 00 02 07 00 ff 06 00
    #  00 00 00 02 02 0f 00 16 1b 02 03 09 06 01 00 03 07 00 ff 06
    #  00 00 00 00 02 02 0f 00 16 1d 02 03 09 06 01 00 04 07 00 ff
    #  06 00 00 00 00 02 02 0f 00 16 1d 02 03 09 06 01 00 1f 07 00
    #  ff 10 00 00 02 02 0f ff 16 21 02 03 09 06 01 00 20 07 00 ff
    #  12 09 6b 02 02 0f ff 16 23 73 00 7e

    current_list = OneList()
    for i in range(noof_records):
        print(f"Processing ROW/record {i}")
        retval_hex, retval_str, the_row = decode_row(byte_data)
        print(f"<<ROW>> {the_row}")
        current_list.add_row(the_row)
        print(f"XXXXXXXX\n\nROW/record {i} is processed\n\n\n\n")

        print(f"{retval_hex}    {retval_str}")

    print("======================")
    print("======================")
    print("======================")
    print(current_list)
    print("======================")
    print("======================")
    print("======================")
    return "<Done."


def extract_string(byte_data):
    _, length = whatsit(byte_data)
    # code, length, <length bytes of data> ==> length + 2
    hstr = hexify(byte_data[: length + 2])
    str_str = bytes_printable(byte_data[: length + 2])
    print(hexify(byte_data[:40], breakit=False))
    del byte_data[: length + 2]
    print(hexify(byte_data[:40], breakit=False))
    print("^^7^^77^7777^^^^")
    return hstr, str_str, str_str


def extract_visible_string(byte_data):
    print("Visible string")
    return extract_string(byte_data)


def extract_octet_string(byte_data):
    print("Octet string")
    return extract_string(byte_data)


def extract_double(byte_data):
    print("\n\ndouble - four bytes")
    retval_hex = hexify(byte_data[1:5])
    retval_str = "d d d d"
    # byte_data[0] is the "double"-marker
    retval_v = (byte_data[1] << 24) + (byte_data[2] << 16) + (byte_data[3] << 8) + byte_data[4]
    del byte_data[:5]

    return retval_hex, retval_str, retval_v


def extract_int(byte_data):
    retval_hex = hexify(byte_data[:2])
    retval_str = f"i {byte_data[1]}"
    del byte_data[:2]
    return retval_hex, retval_str, byte_data[1]


def extract_long(byte_data):
    retval_hex = hexify(byte_data[:3])
    retval_str = f"L {byte_data[1:2]}"
    retval_v = (byte_data[2] << 8) + byte_data[1]
    del byte_data[:3]
    return retval_hex, retval_str, retval_v


def extract_enum(byte_data):
    retval_hex = hexify(byte_data[:2])
    retval_str = f" {PhysicalUnits(byte_data[1])}"

    del byte_data[:2]
    return retval_hex, retval_str, ''


def extract_next_basic_data(byte_data, current_row, retval_hex, retval_str):
    retval_h = ""
    retval_s = ""
    retval_v = ""
    print(f"About to extract data from: {hexify(byte_data)}")
    data_type = DataType(byte_data[0])
    print(f"Found data type: {data_type.name}")
    match data_type:
        case DataType.OCTET_STRING:
            retval_h, retval_s, retval_v = extract_octet_string(byte_data)
        case DataType.VISIBLE_STRING:
            retval_h, retval_s, retval_v = extract_visible_string(byte_data)
        case DataType.DOUBLE_LONG_UNSIGNED:
            retval_h, retval_s, retval_v = extract_double(byte_data)
        case DataType.INTEGER:
            retval_h, retval_s, retval_v = extract_int(byte_data)
        case DataType.LONG:
            retval_h, retval_s, retval_v = extract_long(byte_data)
        case DataType.LONG_UNSIGNED:
            retval_h, retval_s, retval_v = extract_long(byte_data)
        case DataType.ENUM:
            retval_h, retval_s, retval_v = extract_enum(byte_data)

        case _:
            print(f"get_next_basic_data  type is: {DataType(byte_data[0])} because: {hexify(byte_data[:10])}")
            return data_type

    current_row.add_data(retval_h, retval_s, retval_v)

    print(f"Basic data ({data_type.name}): hex:{retval_h}  <===> str:{retval_s}")
    retval_hex += retval_h
    retval_str += retval_s
    return data_type


def decode_struct(byte_data, current_row, retval_hex="", retval_str="", depth=0):
    # print(f">>> decode_struct() depth={depth} .>>>  {hexify(byte_data[:25], breakit=False)}")
    _, noof_elements = whatsit(byte_data)
    del byte_data[:2]
    dpth = depth
    print(f">>> decode_struct() {noof_elements} elems, depth={depth} .>>>  {hexify(byte_data[:25], breakit=False)}")

    for counter in range(noof_elements):
        next_data_type = extract_next_basic_data(byte_data, current_row, retval_hex, retval_str)
        if next_data_type == DataType.STRUCTURE:
            retval_hex += hexify(byte_data[:2])
            retval_str += bytes_printable(byte_data[:2])
            del byte_data[:2]
            dpth += 1
            h, s = decode_struct(byte_data, current_row, depth=dpth, retval_hex=retval_hex, retval_str=retval_str)
            retval_hex += h
            retval_str += s
            dpth -= 1
        else:
            print(f"Just handled data of type: {next_data_type.name}")

    print(f"<<<<< decode_struct() - depth:{dpth}")

    return retval_hex, retval_str


def decode_row(byte_data):
    print(f">>> decode_row(): {hexify(byte_data, breakit=False)}....")
    retval_hex = 'NOT STARTED '
    retval_str = 'NOT STARTED '
    current_row = OneRecord()
    try:
        retval_str = ""
        row_type, noof_elems = whatsit(byte_data)
        text = f"it is a {row_type}, of {noof_elems} items"
        print(text)

        retval_hex = hexify(byte_data[:2])
        retval_str = bytes_printable(byte_data[:2])
        current_row.add_data(retval_hex, retval_str, text)

        if row_type == DataType.STRUCTURE:
            for j in range(noof_elems):
                print(f"ROW number: {j}")
                retval_h, retval_s = decode_struct(byte_data, current_row)
                retval_hex += retval_h
                retval_str += retval_s
                j += 1
        elif row_type == DataType.UNKNOWN and byte_data[2] == 0x7e:
            print(f"End of list for: {hexify(byte_data)}")
        else:
            print(f"Done: {hexify(byte_data)}")

        print(f"1ROW/RESULT===>")
        # print(f"ROW/RESULT===> {retval_hex} <==> {retval_str}")
        print(f"2ROW/RESULT===>")
    except Exception as ee_ee:
        print(f"ROW/RESULT===>")
        print(f"Exception in main loop: {ee_ee}\n{ee_ee.__class__}")
        traceback.print_exc()
        print(f"ROW/RESULT===> {retval_hex} <==> {retval_str}")
        print(f"ROW/RESULT===>")

    return retval_hex, retval_str, current_row


def which_list(this_list):
    if len(this_list) > 300:
        return "List 3"
    elif len(this_list) > 100:
        return "List 2"
    elif len(this_list) > 40:
        return "List 1"


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
            if byte_data[local_ix] == 0x7E:
                count_7es += 1
                if count_7es == 1:
                    if byte_data[local_ix + 1] == 0x7E:
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


def after_hdlc(byte_data):
    retval = "Xdlc>"
    for index in range(6):
        string_part = " %02x" % (byte_data[index])
        retval += string_part
    retval += "\n"

    del byte_data[:6]
    return retval


def hdlc(byte_data):
    """
    Extract the hdlc header.

    Parameters
    ----------
    byte_data : _type_
        _description_

    Returns
    -------
    _type_
        _description_
    """
    print("\n\n\nHDLC\n\n\n")
    retval = "hdlc>"
    for index in range(12):
        s = " %02x" % (byte_data[index])
        retval += s
    retval += "\n"

    del byte_data[:12]
    return retval


def find_start(byte_data):
    """
    Remove everything from byte stream leading up to the first 0x7e.

    :param byte_data:
    :return:
    """
    if len(byte_data) < 2:
        return False

    while len(byte_data) >= 2:
        if byte_data[0] == 0x7E and byte_data[1] == 0x7E:
            # Throw away the first 7e. The second one will be the start of a message
            throwing = byte_data.pop(0)
            return True
        else:
            throwing = byte_data.pop(0)
            print("Throwing: 0x%02x" % throwing)
    return False


def extract_next_message(byte_data):
    retval = []
    if byte_data[0] == 0x7E and byte_data[1] != 0x7E:
        print(".")
    else:
        find_start(byte_data)

    the_count = 0
    with contextlib.suppress(Exception):
        while the_count < 2:
            the_byte = byte_data.pop(0)
            if the_byte == 0x7E:
                the_count += 1

            retval.append(the_byte)
    print("Extracted message length: %d" % len(retval))
    print(f"List: {which_list(retval)}")

    return retval
