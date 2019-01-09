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
"""Parse and format date and time.

SYNOPSIS
    # 1. Print date time point
    # 1.1 Current date time with an optional offset
    isodate [--offset=OFFSET]
    isodate now [--offset=OFFSET]
    isodate ref [--offset=OFFSET]
    # 1.2 Task cycle date time with an optional offset
    #     Assume: export ISODATEREF=20371225T000000Z
    isodate -c [--offset=OFFSET]
    isodate -c ref [--offset=OFFSET]
    # 1.3 A specific date time with an optional offset
    isodate 20380119T031407Z [--offset=OFFSET]

    # 2. Print duration
    # 2.1 Between now (+ OFFSET1) and a future date time (+ OFFSET2)
    isodate now [--offset1=OFFSET1] 20380119T031407Z [--offset2=OFFSET2]
    # 2.2 Between a date time in the past and now
    isodate 19700101T000000Z now
    # 2.3 Between task cycle time (+ OFFSET1) and a future date time
    #     Assume: export ISODATEREF=20371225T000000Z
    isodate -c ref [--offset1=OFFSET1] 20380119T031407Z
    # 2.4 Between task cycle time and now (+ OFFSET2)
    #     Assume: export ISODATEREF=20371225T000000Z
    isodate -c ref now [--offset2=OFFSET2]
    # 2.5 Between a date time in the past and the task cycle date time
    #     Assume: export ISODATEREF=20371225T000000Z
    isodate -c 19700101T000000Z ref
    # 2.6 Between 2 specific date times
    isodate 19700101T000000Z 20380119T031407Z

    # 3.  Convert ISO8601 duration
    # 3.1 Into the total number of hours (H), minutes (M) or seconds (S)
    #     it represents, preceed negative durations with a double backslash
    #     (e.g. \\-PT1H)
    isodate --as-total=s PT1H

DESCRIPTION
    Parse and print 1. a date time point or 2. a duration.

    1. With 0 or 1 argument. Print the current or the specified date time
       point with an optional offset.

    2. With 2 arguments. Print the duration between the 2 arguments.

CALENDAR MODE
    The calendar mode is determined (in order) by:

    1. The `--calendar=MODE` option.
    2. The `ISODATECALENDAR` environment variable.
    3. Default to "gregorian".

ENVIRONMENT VARIABLES
    ISODATECALENDAR=gregorian|360day|365day|366day
        Specify the calendar mode.
    ISODATEREF
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
from datetime import datetime
import os
import re
import sys
from isodatetime.data import Calendar, Duration, get_timepoint_for_now
from isodatetime.dumpers import TimePointDumper
from isodatetime.parsers import TimePointParser, DurationParser


class OffsetValueError(ValueError):

    """Bad offset value."""

    def __str__(self):
        return "%s: bad offset value" % self.args[0]


class DateTimeOperator(object):

    """A class to parse and print date string with an offset."""

    CURRENT_TIME_DUMP_FORMAT = "CCYY-MM-DDThh:mm:ss+hh:mm"
    CURRENT_TIME_DUMP_FORMAT_Z = "CCYY-MM-DDThh:mm:ssZ"

    ENV_REF = "ISODATEREF"
    ENV_CALENDAR_MODE = "ISODATECALENDAR"

    # strptime formats and their compatibility with the ISO 8601 parser.
    PARSE_FORMATS = [
        ("%a %b %d %H:%M:%S %Y", True),     # ctime
        ("%a %b %d %H:%M:%S %Z %Y", True),  # Unix "date"
        ("%Y-%m-%dT%H:%M:%S", False),       # ISO8601, extended
        ("%Y%m%dT%H%M%S", False),           # ISO8601, basic
        ("%Y%m%d%H", False)                 # Cylc (current)
    ]

    REC_OFFSET = re.compile(r"""\A[\+\-]?(?:\d+[wdhms])+\Z""", re.I)
    REC_OFFSET_FIND = re.compile(r"""(?P<num>\d+)(?P<unit>[wdhms])""")

    STR_NOW = "now"
    STR_REF = "ref"

    UNITS = {
        "w": "weeks",
        "d": "days",
        "h": "hours",
        "m": "minutes",
        "s": "seconds",
    }

    def __init__(
        self,
        parse_format=None,
        utc_mode=False,
        calendar_mode=None,
        ref_point_str=None,
    ):
        """Constructor.

        parse_format -- If specified, parse with the specified format.
                        Otherwise, parse with one of the format strings in
                        self.PARSE_FORMATS. The format should be a string
                        compatible to strptime(3).

        utc_mode -- If True, parse/print in UTC mode rather than local or
                    other timezones.

        calendar_mode -- Set calendar mode, for isodatetime.data.Calendar.

        ref_point_str -- Set the reference time point for operations.
                         If not specified, operations use current date time.

        """
        self.parse_formats = self.PARSE_FORMATS
        self.custom_parse_format = parse_format
        self.utc_mode = utc_mode
        if self.utc_mode:
            assumed_time_zone = (0, 0)
        else:
            assumed_time_zone = None

        self.set_calendar_mode(calendar_mode)

        self.time_point_dumper = TimePointDumper()
        self.time_point_parser = TimePointParser(
            assumed_time_zone=assumed_time_zone)
        self.duration_parser = DurationParser()

        if ref_point_str is None:
            self.ref_point_str = os.getenv(self.ENV_REF)
        else:
            self.ref_point_str = ref_point_str

    def date_format(self, print_format, time_point=None):
        """Reformat time_point according to print_format.

        time_point -- The time point to format.
                      Otherwise, use ref date time.

        """
        if time_point is None:
            time_point = self.date_parse()[0]
        if print_format is None:
            return str(time_point)
        if "%" in print_format:
            try:
                return time_point.strftime(print_format)
            except ValueError:
                return self.get_datetime_strftime(time_point, print_format)
        return self.time_point_dumper.dump(time_point, print_format)

    def date_parse(self, time_point_str=None):
        """Parse time_point_str.

        Return (t, format) where t is a isodatetime.data.TimePoint object and
        format is the format that matches time_point_str.

        time_point_str -- The time point string to parse.
                          Otherwise, use ref time.

        """
        if time_point_str is None or time_point_str == self.STR_REF:
            time_point_str = self.ref_point_str
        if time_point_str is None or time_point_str == self.STR_NOW:
            time_point = get_timepoint_for_now()
            time_point.set_time_zone_to_local()
            if self.utc_mode or time_point.get_time_zone_utc():  # is in UTC
                parse_format = self.CURRENT_TIME_DUMP_FORMAT_Z
            else:
                parse_format = self.CURRENT_TIME_DUMP_FORMAT
        elif self.custom_parse_format is not None:
            parse_format = self.custom_parse_format
            time_point = self.strptime(time_point_str, parse_format)
        else:
            parse_formats = list(self.parse_formats)
            time_point = None
            while parse_formats:
                parse_format, should_use_datetime = parse_formats.pop(0)
                try:
                    if should_use_datetime:
                        time_point = self.get_datetime_strptime(
                            time_point_str,
                            parse_format)
                    else:
                        time_point = self.time_point_parser.strptime(
                            time_point_str,
                            parse_format)
                    break
                except ValueError:
                    pass
            if time_point is None:
                time_point = self.time_point_parser.parse(
                    time_point_str,
                    dump_as_parsed=True)
                parse_format = time_point.dump_format
        if self.utc_mode:
            time_point.set_time_zone_to_utc()
        return time_point, parse_format

    def date_shift(self, time_point=None, offset=None):
        """Return a date string with an offset.

        time_point -- A time point or time point string.
                      Otherwise, use current time.

        offset -- If specified, it should be a string containing the offset
                  that has the format "[+/-]nU[nU...]" where "n" is an
                  integer, and U is a unit matching a key in self.UNITS.

        """
        if time_point is None:
            time_point = self.date_parse()[0]
        # Offset
        if offset:
            sign = "+"
            if offset.startswith("-") or offset.startswith("+"):
                sign = offset[0]
                offset = offset[1:]
            if offset.startswith("P"):
                # Parse and apply.
                try:
                    duration = self.duration_parser.parse(offset)
                except ValueError:
                    raise OffsetValueError(offset)
                if sign == "-":
                    time_point -= duration
                else:
                    time_point += duration
            else:
                # Backwards compatibility for e.g. "-1h"
                if not self.is_offset(offset):
                    raise OffsetValueError(offset)
                for num, unit in self.REC_OFFSET_FIND.findall(offset.lower()):
                    num = int(num)
                    if sign == "-":
                        num = -num
                    key = self.UNITS[unit]
                    time_point += Duration(**{key: num})

        return time_point

    def date_diff(self, time_point_1=None, time_point_2=None):
        """Return (duration, is_negative) between two TimePoint objects.

        duration -- is a Duration instance.
        is_negative -- is "-" if time_point_2 is in the past of time_point_1.
        """
        if time_point_2 < time_point_1:
            return (time_point_1 - time_point_2, "-")
        else:
            return (time_point_2 - time_point_1, "")

    @classmethod
    def date_diff_format(cls, print_format, duration, sign):
        """Format a duration."""
        if print_format:
            delta_lookup = {
                "y": duration.years,
                "m": duration.months,
                "d": duration.days,
                "h": duration.hours,
                "M": duration.minutes,
                "s": duration.seconds,
            }
            expression = ""
            for item in print_format:
                if item in delta_lookup:
                    if float(delta_lookup[item]).is_integer():
                        expression += str(int(delta_lookup[item]))
                    else:
                        expression += str(delta_lookup[item])
                else:
                    expression += item
            return sign + expression
        else:
            return sign + str(duration)

    @staticmethod
    def get_calendar_mode():
        """Get current calendar mode."""
        return Calendar.default().mode

    def is_offset(self, offset):
        """Return True if the string offset can be parsed as an offset."""
        return (self.REC_OFFSET.match(offset) is not None)

    @classmethod
    def set_calendar_mode(cls, calendar_mode=None):
        """Set calendar mode for subsequent operations.

        Raise KeyError if calendar_mode is invalid.

        """
        if not calendar_mode:
            calendar_mode = os.getenv(cls.ENV_CALENDAR_MODE)
        if calendar_mode and calendar_mode in Calendar.MODES:
            Calendar.default().set_mode(calendar_mode)

    def strftime(self, time_point, print_format):
        """Use either the isodatetime or datetime strftime time formatting."""
        try:
            return time_point.strftime(print_format)
        except ValueError:
            return self.get_datetime_strftime(time_point, print_format)

    def strptime(self, time_point_str, parse_format):
        """Use either the isodatetime or datetime strptime time parsing."""
        try:
            return self.time_point_parser.strptime(
                time_point_str, parse_format)
        except ValueError:
            return self.get_datetime_strptime(time_point_str, parse_format)

    @classmethod
    def get_datetime_strftime(cls, time_point, print_format):
        """Use the datetime library's strftime as a fallback."""
        calendar_date = time_point.copy().to_calendar_date()
        year, month, day = calendar_date.get_calendar_date()
        hour, minute, second = time_point.get_hour_minute_second()
        microsecond = int(1.0e6 * (second - int(second)))
        hour = int(hour)
        minute = int(minute)
        second = int(second)
        date_time = datetime(
            year, month, day, hour, minute, second, microsecond)
        return date_time.strftime(print_format)

    def get_datetime_strptime(self, time_point_str, parse_format):
        """Use the datetime library's strptime as a fallback."""
        date_time = datetime.strptime(time_point_str, parse_format)
        return self.time_point_parser.parse(date_time.isoformat())

    def process_time_point_str(
        self,
        time_point_str=None,
        offsets=None,
        print_format=None,
    ):
        """Process time point string with optional offsets."""
        time_point, parse_format = self.date_parse(time_point_str)
        if offsets:
            for offset in offsets:
                time_point = self.date_shift(time_point, offset)
        if print_format:
            return self.date_format(print_format, time_point)
        elif parse_format:
            return self.date_format(parse_format, time_point)
        else:
            return str(time_point)

    def diff_time_point_strs(
        self,
        time_point_str_1,
        time_point_str_2,
        offsets1=None,
        offsets2=None,
        print_format=None,
        duration_print_format=None,
    ):
        """Calculate duration between 2 time point strings.

        Each time point string may have optional offsets.
        """
        time_point_1 = self.date_parse(time_point_str_1)[0]
        time_point_2 = self.date_parse(time_point_str_2)[0]
        if offsets1:
            for offset in offsets1:
                time_point_1 = self.date_shift(time_point_1, offset)
        if offsets2:
            for offset in offsets2:
                time_point_2 = self.date_shift(time_point_2, offset)
        duration, sign = self.date_diff(time_point_1, time_point_2)
        out = self.date_diff_format(print_format, duration, sign)
        if duration_print_format:
            return self.format_duration_str(out)
        else:
            return out

    def format_duration_str(self, duration_str, duration_print_format):
        """Parse duration string, return as total of a unit.

        Unit can be H, M or S (for hours, minutes or seconds).
        """
        duration = self.duration_parser.parse(
            duration_str.replace('\\', ''))  # allows negative durations
        time = duration.get_seconds()
        options = {'S': time, 'M': time / 60, 'H': time / 3600}
        if duration_print_format.upper() in options:
            # supplied duration format is valid (upper removes case-sensitivity)
            return options[duration_print_format.upper()]
        else:
            # supplied duration format not valid
            raise ValueError(
                'Invalid duration print format, '
                'should use one of H, M, S for (hours, minutes, seconds)'
            )


def main():
    """Implement "isodate" command."""
    arg_parser = ArgumentParser(
        prog='isodate',
        formatter_class=RawDescriptionHelpFormatter,
        description=__doc__)
    for o_args, o_kwargs in [
        [
            ["items"],
            {
                "nargs": "*",
                "help": "Time point or duration string",
                "metavar": "ITEM",
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
                "metavar": "MODE",
                "help": "Set the calendar mode.",
            },
        ],
        [
            ["--diff"],
            {
                "action": "store",
                "dest": "diff",
                "default": None,
                "help": "Set a datetime to subtract from DATE-TIME.",
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
            out = self.diff_time_point_strs(
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
