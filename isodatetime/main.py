# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (C) 2013-2018 British Crown (Met Office) & Contributors.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------
"""Parse and format date-time points and durations.

SYNOPSIS
    # 1. Print date time point
    # 1.1 Current date time with an optional offset
    isodatetime [--offset=OFFSET]
    isodatetime now [--offset=OFFSET]
    isodatetime ref [--offset=OFFSET]
    # 1.2 Task cycle date time with an optional offset
    #     Assume: export ISODATETIMEREF=20371225T000000Z
    isodatetime -c [--offset=OFFSET]
    isodatetime -c ref [--offset=OFFSET]
    # 1.3 A specific date time with an optional offset
    isodatetime 20380119T031407Z [--offset=OFFSET]

    # 2. Print duration
    # 2.1 Between now (+ OFFSET1) and a future date time (+ OFFSET2)
    isodatetime now [--offset1=OFFSET1] 20380119T031407Z [--offset2=OFFSET2]
    # 2.2 Between a date time in the past and now
    isodatetime 19700101T000000Z now
    # 2.3 Between task cycle time (+ OFFSET1) and a future date time
    #     Assume: export ISODATETIMEREF=20371225T000000Z
    isodatetime -c ref [--offset1=OFFSET1] 20380119T031407Z
    # 2.4 Between task cycle time and now (+ OFFSET2)
    #     Assume: export ISODATETIMEREF=20371225T000000Z
    isodatetime -c ref now [--offset2=OFFSET2]
    # 2.5 Between a date time in the past and the task cycle date time
    #     Assume: export ISODATETIMEREF=20371225T000000Z
    isodatetime -c 19700101T000000Z ref
    # 2.6 Between 2 specific date times
    isodatetime 19700101T000000Z 20380119T031407Z

    # 3.  Convert ISO8601 duration
    # 3.1 Into the total number of hours (H), minutes (M) or seconds (S)
    #     it represents, preceed negative durations with a double backslash
    #     (e.g. \\-PT1H)
    isodatetime --as-total=s PT1H

DESCRIPTION
    Parse and print 1. a date time point or 2. a duration.

    1. With 0 or 1 argument. Print the current or the specified date time
       point with an optional offset.

    2. With 2 arguments. Print the duration between the 2 arguments.

CALENDAR MODE
    The calendar mode is determined (in order) by:

    1. The `--calendar=MODE` option.
    2. The `ISODATETIMECALENDAR` environment variable.
    3. Default to "gregorian".

ENVIRONMENT VARIABLES
    ISODATETIMECALENDAR=gregorian|360day|365day|366day
        Specify the calendar mode.
    ISODATETIMEREF
        Specify the current cycle time of a task in a suite. If the
        `--use-task-cycle-time` option is set, the value of this environment
        variable is used by the command as the reference time instead of the
        current time.

OFFSET FORMAT
    `OFFSET` must follow the ISO 8601 duration representations such as
    `PnW` or `PnYnMnDTnHnMnS - P` followed by a series of `nU` where `U` is
    the unit (`Y`, `M`, `D`, `H`, `M`, `S`) and `n` is a positive integer,
    where `T` delimits the date series from the time series if any time units
    are used. `n` may also have a decimal (e.g. `PT5.5M`) part for a unit
    provided no smaller units are supplied. It is not necessary to
    specify zero values for units. If `OFFSET` is negative, prefix a `-`.
    For example:

    * `P6D` - 6 day offset
    * `PT6H` - 6 hour offset
    * `PT1M` - 1 minute offset
    * `-PT1M` - (negative) 1 minute offset
    * `P3M` - 3 month offset
    * `P2W` - 2 week offset (note no other units may be combined with weeks)
    * `P2DT5.5H` - 2 day, 5.5 hour offset
    * `-P2YT4S` - (negative) 2 year, 4 second offset

    The following deprecated syntax is supported:
    `OFFSET` in the form `nU` where `U` is the unit (`w` for weeks, `d` for
    days, `h` for hours, `m` for minutes and `s` for seconds) and `n` is a
    positive or negative integer.

PARSE FORMAT
    The format for parsing a date time point should be compatible with the
    POSIX strptime template format (see the strptime command help), with the
    following subset supported across all date/time ranges:

    `%F`, `%H`, `%M`, `%S`, `%Y`, `%d`, `%j`, `%m`, `%s`, `%z`

    If not specified, the system will attempt to parse `DATE-TIME` using
    the following formats:

    * ctime: `%a %b %d %H:%M:%S %Y`
    * Unix date: `%a %b %d %H:%M:%S %Z %Y`
    * Basic ISO8601: `%Y-%m-%dT%H:%M:%S`, `%Y%m%dT%H%M%S`
    * Cylc: `%Y%m%d%H`

    If none of these match, the date time point will be parsed according to
    the full ISO 8601 date/time standard.

PRINT FORMAT
    For printing a date time point, the print format will default to the same
    format as the parse format. Also supports the isodatetime library dump
    syntax for these operations which follows ISO 8601 example syntax - for
    example:

    * `CCYY-MM-DDThh:mm:ss` -> `1955-11-05T09:28:00`,
    * `CCYY` -> `1955`,
    * `CCYY-DDD` -> `1955-309`,
    * `CCYY-Www-D` -> `1955-W44-6`.

    Usage of this ISO 8601-like syntax should be as ISO 8601-compliant
    as possible.

    Note that specifying an explicit timezone in this format (e.g.
    `CCYY-MM-DDThh:mm:ss+0100` or `CCYYDDDThhmmZ` will automatically
    adapt the date/time to that timezone i.e. apply the correct
    hour/minute UTC offset.

    For printing a duration, the following can be used in format
    statements:

    * `y`: years
    * `m`: months
    * `d`: days
    * `h`: hours
    * `M`: minutes
    * `s`: seconds

    For example, for a duration `P57DT12H` - `y,m,d,h` -> `0,0,57,12`
"""


from argparse import ArgumentParser, RawDescriptionHelpFormatter
import sys

from .datetimeoper import DateTimeOperator


def main():
    """Implement "isodatetime" command."""
    arg_parser = ArgumentParser(
        prog='isodatetime',
        formatter_class=RawDescriptionHelpFormatter,
        description=__doc__)
    for o_args, o_kwargs in [
        [
            ["items"],
            {
                "help": "Time point or duration string",
                "metavar": "ITEM",
                "nargs": "*",
            },
        ],
        [
            ["--as-total"],
            {
                "action": "store",
                "dest": "duration_print_format",
                "help": "Express a duration string in the provided units.",
            },
        ],
        [
            ["--calendar"],
            {
                "action": "store",
                "choices": ["360day", "365day", "366day", "gregorian"],
                "help": "Set the calendar mode.",
                "metavar": "MODE",
            },
        ],
        [
            ["--offset1", "--offset", "-s", "-1"],
            {
                "action": "append",
                "dest": "offsets1",
                "metavar": "OFFSET",
                "help": "Specify offsets for 1st date time point.",
            },
        ],
        [
            ["--offset2", "-2"],
            {
                "action": "append",
                "dest": "offsets2",
                "metavar": "OFFSET",
                "help": "Specify offsets for 2nd date time point.",
            },
        ],
        [
            ["--parse-format", "-p"],
            {
                "metavar": "FORMAT",
                "help": "Specify the format for parsing inputs.",
            },
        ],
        [
            ["--print-format", "--format", "-f"],
            {
                "metavar": "FORMAT",
                "help": "Specify the format for printing results.",
            },
        ],
        [
            ["--ref", "-R"],
            {
                "action": "store",
                "dest": "ref_point_str",
                "help": "Specify a reference point string.",
                "metavar": "REF",
            },
        ],
        [
            ["--utc", "-u"],
            {
                "action": "store_true",
                "default": False,
                "dest": "utc_mode",
                "help": "Switch on UTC mode.",
            },
        ],
    ]:
        arg_parser.add_argument(*o_args, **o_kwargs)
    args = arg_parser.parse_args()
    date_time_oper = DateTimeOperator(
        parse_format=args.parse_format,
        utc_mode=args.utc_mode,
        calendar_mode=args.calendar,
        ref_point_str=args.ref_point_str)

    try:
        if len(args.items) >= 2:
            out = date_time_oper.diff_time_point_strs(
                args.items[0],
                args.items[1],
                args.offsets1,
                args.offsets2,
                args.print_format,
                args.duration_print_format)
        elif args.items and args.duration_print_format:
            out = date_time_oper.format_duration_str(
                args.items[0], args.duration_print_format)
        else:
            time_point_str = None
            if args.items:
                time_point_str = args.items[0]
            out = date_time_oper.process_time_point_str(
                time_point_str, args.offsets1, args.print_format)
    except ValueError as exc:
        sys.exit(exc)
    else:
        print(out)


if __name__ == "__main__":
    main()
