# pylint: disable=consider-using-enumerate, missing-docstring, consider-using-f-string
import datetime
import string


def get_now():
    return f'{[datetime.datetime.now().strftime("%a, %d %B %Y %H:%M:%S")]}'


def get_simple_print_byte_array(byte_data):
    outs = ""
    for ix in range(len(byte_data)):
        s = " %02x" % (byte_data[ix])
        if (ix + 1) % 20 == 0:
            s += "\n"
        outs += s
    return outs


def simple_print_byte_array(byte_data):
    outs = get_simple_print_byte_array(byte_data)
    print(f" outs\n{outs}")
    readable_string = ""
    for ix, s in enumerate(byte_data, start=1):
        if ix % 20 == 0:
            readable_string += "\n"
        readable_string += "%-3s" % printable_byte(s)

    print("=== readable ====")
    print(readable_string)
    print("^^^^^^^^^^^^^^^^^")
    return outs


def printable_byte(one_byte):
    # print("A")
    pcand = chr(one_byte)
    # print(f"CNAD:{pcand}")
    return_printable = " . "
    if pcand in string.printable:
        return_printable = pcand
        if return_printable == "\t":
            return_printable = " "
        if return_printable == " ":
            return_printable = " "
        if return_printable == "\r":
            return_printable = " "
    # print(f"Returning: {return_printable}")
    return return_printable


def hexify(byte_data, breakit=True):
    hex_string = ""
    for index in range(len(byte_data)):
        byte_as_hex = " %02x" % (byte_data[index])
        if breakit and (index + 1) % 20 == 0:
            byte_as_hex += "\n"
        hex_string += byte_as_hex
    return hex_string


def bytes_printable(byte_data):
    printable_string = ""
    for index, the_byte in enumerate(byte_data, start=1):
        if index % 20 == 0:
            printable_string += "\n"
        printable_string += "%-3s" % printable_byte(the_byte)
    return printable_string


def find_start(byte_data):
    """
    Remove everything from byte stream leading up to the first 0x7e
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
