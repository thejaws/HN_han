# pylint: disable=consider-using-enumerate, missing-docstring, consider-using-f-string
from enum import Enum
from han_utils import hexify, bytes_printable


class DataType(Enum):
    NULL_DATA = 0
    BOOLEAN = 3
    BIT_STRING = 4
    DOUBLE_LONG = 5
    DOUBLE_LONG_UNSIGNED = 6
    OCTET_STRING = 9
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
    COMPACT_ARRAY = 19


class PhysicalUnits(Enum):
    POWER = 27
    VA = 28
    VAR = 29
    ACTIVE_ENERGY = 30
    VARH = 32
    AMPERE = 33
    VOLTAGE = 35


def strip_type_length(data):
    complex_data_type, _ = whatsit(data)
    hard_coded_length = False

    if complex_data_type in [DataType.DOUBLE_LONG, DataType.DOUBLE_LONG_UNSIGNED]:
        hard_coded_length = True
    elif complex_data_type in [DataType.INTEGER, DataType.UNSIGNED]:
        hard_coded_length = True
    elif complex_data_type in [DataType.LONG]:
        hard_coded_length = True

    if hard_coded_length:
        del data[:1]
    else:
        del data[:2]


def whatsit(data):
    noof_elements = 0
    complex_data_type = DataType(data[0])

    if complex_data_type in [DataType.DOUBLE_LONG, DataType.DOUBLE_LONG_UNSIGNED]:
        noof_elements = 4
    elif complex_data_type in [DataType.INTEGER, DataType.UNSIGNED]:
        noof_elements = 1
    elif complex_data_type in [DataType.LONG]:
        noof_elements = 2
    else:
        noof_elements = data[1]

    return complex_data_type, noof_elements


# def details(data):
#     data_type = data[0]
#     noof_elements = data[1]


def the_payload(byte_data):
    """
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
    retval = "Xxxx>"
    what, noof_records = whatsit(byte_data)
    print(f"What: {what} - Noof Records: {noof_records}")
    print("%02x %02x" % (byte_data[0], byte_data[1]))

    for ix in range(2):
        s = " %02x" % (byte_data[ix])
        retval += s
    retval += "\n"
    retval += "Payl>"

    # del byte_data[:2]
    strip_type_length(byte_data)

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

    for i in range(noof_records):
        print(f"Processing ROW/record {i}")
        retval_hex, retval_str = decode_row(byte_data)
        print(f"{retval_hex}    {retval_str}")
    return "<Done."


def decode_struct(elems, byte_data):
    print(f"decoding struct  .>>>  {hexify(byte_data[:25], breakit=False)}")
    retval_hex = ""
    retval_str = ""

    for _ in range(elems):
        what, length = whatsit(byte_data)
        print(f"ds - What: {what} - length:{length}")
        retval_hex += hexify(byte_data[:2])
        retval_str += bytes_printable(byte_data[:2])
        strip_type_length(byte_data)

        print(f"Now >>> retval_hex:{retval_hex} <-----> {retval_str}")
        print("Then add data")
        retval_hex += f" Data: {hexify(byte_data[:length])}"
        retval_str += f"{bytes_printable(byte_data[:length])}"
        print(f"Now >>> retval_hex: {retval_hex} <-----> {retval_str}")
        print(f"Aremainder: {hexify(byte_data[:40])}")
        del byte_data[:length]
        print(f"Bremainder: {hexify(byte_data[:40])}")

    return retval_hex, retval_str


def decode_row(byte_data):
    print(f"ROW .... decoding ... {hexify(byte_data, breakit=False)}....")
    retval_str = ""
    what, elems = whatsit(byte_data)
    print(f"it is  a {what}, of {elems} items")
    retval_hex = hexify(byte_data[:2])
    retval_str = bytes_printable(byte_data[:2])
    strip_type_length(byte_data)

    if what == DataType.STRUCTURE:
        for _ in range(elems):
            retval_h, retval_s = decode_struct(elems, byte_data)
            retval_hex += retval_h
            retval_str += retval_s

    print(f"ROW/RESULT===>{retval_hex} <==> {retval_str}")

    return retval_hex, retval_str


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
    for ix in range(6):
        s = " %02x" % (byte_data[ix])
        retval += s
    retval += "\n"

    del byte_data[0:6]
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
    retval = "hdlc>"
    for ix in range(12):
        s = " %02x" % (byte_data[ix])
        retval += s
    retval += "\n"

    del byte_data[0:12]
    return retval


def find_start(byte_data):
    """
    Remove everything from byte stream leading up to the first 0x7e
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
    while the_count < 2:
        the_byte = byte_data.pop(0)
        if the_byte == 0x7E:
            the_count += 1

        retval.append(the_byte)

    print("Extracted message length: %d" % len(retval))
    print(f"List: {which_list(retval)}")

    return retval


def extract_next_message(byte_data):
    retval = []
    if byte_data[0] == 0x7E and byte_data[1] != 0x7E:
        print(".")
    else:
        find_start(byte_data)

    the_count = 0
    try:
        while the_count < 2:
            the_byte = byte_data.pop(0)
            if the_byte == 0x7E:
                the_count += 1

            retval.append(the_byte)
    except Exception:
        pass

    print("Extracted message length: %d" % len(retval))
    print(f"List: {which_list(retval)}")

    return retval
