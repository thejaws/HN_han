import sys

line_ix = 0
for filename in sys.argv[1:]:
    print(filename)
    outfile_name = filename + "_decoded.txt"
    with open(filename, "rb") as infile:
        with open(outfile_name, "w") as outfile:
            line_ix = 0
            while (byte := infile.read(1)):
                line_ix += 1
                print("%02x " % (int.from_bytes(byte)), end='')
                outfile.write("%02x " % (int.from_bytes(byte)))
                if line_ix % 40 == 0:
                    print("")
                    outfile.write("\n")
