# pylint: disable=consider-using-enumerate, missing-docstring, consider-using-f-string
import serial
import serial.tools.list_ports as lp
import sys


def list_and_bail():
    print("Fant ingen com port.\nAvslutter.\n\n Ha det bra.")
    for sp in lp.comports():
        print(f"Name: {sp.name} - Description: {sp.description}")
    sys.exit(0)


def get_com_port_name():
    comport_name = "No com port found"
    comport_description = "No description"
    # (sp.device for sp in lp.comports() if "USB" in sp.description or "usb" in sp.name),
    for sp in lp.comports():
        print(sp)
        if "USB" in sp.name.upper() or "USB" in sp.description.upper():
            comport_name = sp.name
            comport_description = sp.description
            break

    return comport_name, comport_description


def get_comport(comport_name=None):
    print(f"given comport >>> {comport_name}")
    if comport_name is None:
        comport_name, description = get_com_port_name()
    else:
        description = "given port"

    # comport_name = "/dev/tty.usbserial-FTFMLUL7"
    print(f"Opening COM port >>>>>  comport: {comport_name}  -   {description}")
    try:
        port = serial.Serial(comport_name, 2400, parity=serial.PARITY_EVEN, timeout=0.1)
        print("Serial port created:")
        print(port)

        port.reset_input_buffer()
        # serialString = ""
    except Exception as ex:
        print(ex)
        list_and_bail()

    return port
