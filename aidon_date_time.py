import datetime

import construct

from han_utils import hexify

OptionalDateTimeByte = construct.ExprAdapter(
    construct.Int8ub,
    decoder=lambda obj, ctx: obj if obj != 0xFF else None,
    encoder=lambda obj, ctx: obj if obj is not None else 0xFF,
)

# See COSEM blue Book section 4.1.6.1 Date and time formats
DateTime = construct.Struct(
    construct.Const(0x09, construct.Int8ub),  # 9 means octet string
    construct.Const(0x0C, construct.Int8ub),  # expect length 12
    "year" / construct.Int16ub,
    "month" / construct.Int8ub,
    "day_of_month" / construct.Int8ub,
    "day_of_week" / construct.Int8ub,
    "hour" / OptionalDateTimeByte,
    "minute" / OptionalDateTimeByte,
    "second" / OptionalDateTimeByte,
    "hundredths_of_second" / OptionalDateTimeByte,
    "deviation"
    / construct.ExprAdapter(
        construct.Int16sb,
        decoder=lambda obj, ctx: obj if obj != -0x8000 else None,
        encoder=lambda obj, ctx: obj if obj is not None else -0x8000,
    )
    * ("Range -720...+720 in minutes of local time to UTC. 0x8000 = not specified"),
    "clock_status_byte" / construct.Peek(OptionalDateTimeByte),
    "clock_status" / construct.If(construct.this.clock_status_byte != 0xFF,
                                  construct.BitStruct(
                                      "invalid_value" / construct.BitsInteger(1) * ("Time could not be recovered after an incident. Detailed conditions are "
                                                                                    "manufacturer specific (for example after the power to the clock has been "
                                                                                    "interrupted). For a valid status, bit 0 shall not be set if bit 1 is set."
                                                                                    ),
                                      "doubtful_value" / construct.BitsInteger(1) * ("Time could be recovered after an incident but the value cannot be guaranteed. "
                                                                                     "Detailed conditions are manufacturer specific. For a valid status, bit 1 shall "
                                                                                     "not be set if bit 0 is set."
                                                                                     ),
                                      "different_clock_base" / construct.BitsInteger(1) * ("Bit is set if the basic timing information for the clock at the actual moment "
                                                                                           "is taken from a timing source different from the source specified in clock_base."
                                                                                           ),
                                      "invalid_clock_status" / construct.BitsInteger(1) * ("This bit indicates that at least one bit of the clock status is invalid. "
                                                                                           "Some bits may be correct. The exact meaning shall be explained in the "
                                                                                           "manufacturer's documentation."
                                                                                           ),
                                      construct.BitsInteger(3), "daylight_saving_active" / construct.BitsInteger(1) * \
                                      ("Flag set to true: the transmitted time contains the daylight saving deviation (summer time)."),
                                  ),
                                  ),
    construct.If(construct.this.clock_status_byte == 0xFF, construct.Int8ub),
    "datetime"
    / construct.Computed(
        lambda ctx: datetime.datetime(
            ctx.year,
            ctx.month,
            ctx.day_of_month,
            ctx.hour,
            ctx.minute,
            ctx.second,
            ctx.hundredths_of_second * 10000
            if ctx.hundredths_of_second is not None
            else 0,
            datetime.timezone(datetime.timedelta(minutes=ctx.deviation * -1))
            if ctx.deviation is not None
            else None,
        )
    ),
)


def obis_bytes_to_datetime(byte_data):
    """
    Convert 12 byte obis to datetime.



    Parameters
    ----------
    bytes : _type_
        _description_
    """
    # Just use the first 14 bytes of data for this
    the_bytes = bytes(byte_data[:14])
    print(f"Date bytes: {hexify(byte_data[:14])}")
    print(f"the bytez: {the_bytes}")
    dt = DateTime.parse(the_bytes)
    return dt.datetime


if __name__ == "__main__":
    a = [9, 0x0c, 7, 0xe7, 5, 8, 1, 12, 0, 0, 0xff, 0x80, 0x0, 0xff]
    b = bytes(a)
    adt = DateTime.parse(b)
    print(adt)
    print("\n\n")
    print(adt.datetime)

# List: List 3
# ======= 2023-05-08 13:00:20.060974 ===============

# List with 17 records
#   0:      02 02     09 06 01 01 00 02 81 ff     0a 0b 41 49 44 4f 4e 5f 56 30 30 30 31                      .  .     1.1.0.2.129.255.     OBIS list version id    AIDON_V0001
#   1:      02 02     09 06 00 00 60 01 00 ff     0a 10 37 33 35 39 39 39 32 39 30 37 33 38 31 32 39 35       .  .     0.0.96.1.0.255.                  Unknown    .7359992907381295
#   2:      02 02     09 06 00 00 60 01 07 ff     0a 04 36 35 34 30                                           .  .     0.0.96.1.7.255.                  Unknown    .6540
#   3:      02 03     09 06 01 00 01 07 00 ff     06 00 00 13 01     02 02     0f 00     16 1b                .  .      1.0.1.7.0.255.     Active power+(Q1+Q4)     4865             .  .      PhysicalUnits.POWER
#   4:      02 03     09 06 01 00 02 07 00 ff     06 00 00 00 00     02 02     0f 00     16 1b                .  .      1.0.2.7.0.255.     Active power-(Q1+Q4)        0             .  .      PhysicalUnits.POWER
#   5:      02 03     09 06 01 00 03 07 00 ff     06 00 00 00 00     02 02     0f 00     16 1d                .  .      1.0.3.7.0.255.  Reactive power+ (Q1+Q2)        0             .  .      PhysicalUnits.VAR
#   6:      02 03     09 06 01 00 04 07 00 ff     06 00 00 01 27     02 02     0f 00     16 1d                .  .      1.0.4.7.0.255.  Reactive power- (Q1+Q2)      295             .  .      PhysicalUnits.VAR
#   7:      02 03     09 06 01 00 1f 07 00 ff     10 00 a7     02 02     0f ff     16 21                      .  .     1.0.31.7.0.255.                      IL1      167             .  .      PhysicalUnits.AMPERE
#   8:      02 03     09 06 01 00 47 07 00 ff     10 00 7c     02 02     0f ff     16 21                      .  .     1.0.71.7.0.255.                      IL3      124             .  .      PhysicalUnits.AMPERE
#   9:      02 03     09 06 01 00 20 07 00 ff     12 09 4b     02 02     0f ff     16 23                      .  .     1.0.32.7.0.255.                      UL1     2379             .  .      PhysicalUnits.VOLTAGE
#  10:      02 03     09 06 01 00 34 07 00 ff     12 09 3d     02 02     0f ff     16 23                      .  .     1.0.52.7.0.255.                      UL2     2365             .  .      PhysicalUnits.VOLTAGE
#  11:      02 03     09 06 01 00 48 07 00 ff     12 09 49     02 02     0f ff     16 23                      .  .     1.0.72.7.0.255.                      UL3     2377             .  .      PhysicalUnits.VOLTAGE
#  12:      02 02     09 06 00 00 01 00 00 ff     09 0c 07 e7 05 08 01 0c 00 00 ff 80 00 ff                   .  .      0.0.1.0.0.255.                    Clock    7.231.5.8.1.12.                  Unknown
#  13:      02 03     09 06 01 00 01 08 00 ff     06 01 05 c0 71     02 02     0f 01     16 1e                .  .      1.0.1.8.0.255.                  A+cumul    17154161             .  .      PhysicalUnits.ACTIVE_ENERGY
#  14:      02 03     09 06 01 00 02 08 00 ff     06 00 03 c5 ef     02 02     0f 01     16 1e                .  .      1.0.2.8.0.255.                  A-cumul    247279             .  .      PhysicalUnits.ACTIVE_ENERGY
#  15:      02 03     09 06 01 00 03 08 00 ff     06 00 00 de 4c     02 02     0f 01     16 20                .  .      1.0.3.8.0.255.                  R+cumul    56908             .  .      PhysicalUnits.VARH
#  16:      02 03     09 06 01 00 04 08 00 ff     06 00 19 f5 16     02 02     0f 01     16 20                .  .      1.0.4.8.0.255.                  A-cumul    1701142             .  .      PhysicalUnits.VARH
