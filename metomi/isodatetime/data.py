# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Copyright (C) British Crown (Met Office) & Contributors.
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
# ----------------------------------------------------------------------------

"""This provides ISO 8601 data model functionality."""


from . import dumpers
from . import timezone
from .exceptions import BadInputError

import operator
from functools import lru_cache


_operator_map = {op.__name__: op for op in [
    operator.eq, operator.lt, operator.le, operator.gt, operator.ge]}


class Calendar:

    """Store constants for Gregorian calendar date-time calculation."""

    SECONDS_IN_MINUTE = 60
    MINUTES_IN_HOUR = 60
    HOURS_IN_DAY = 24
    DAYS_IN_WEEK = 7
    DAYS_IN_MONTHS = None  # This is set up in the set_* methods.
    DAYS_IN_MONTHS_LEAP = None  # This is set up in the set_* methods
    ROUGH_DAYS_IN_MONTH = 30  # Used for duration conversion, nowhere else.
    MAX_WEEKS_IN_YEAR = 53  # In ISO week year, used for truncated dates

    LEAP_YEAR_FACTOR_TRUTHS = [(4, True), (100, False), (400, True)]

    MODE_360 = "360day"
    MODE_360_DAY = "360_day"
    MODE_365 = "365day"
    MODE_365_DAY = "365_day"
    MODE_366 = "366day"
    MODE_366_DAY = "366_day"
    MODE_GREGORIAN = "gregorian"
    DAYS_IN_MONTHS_360 = 12 * (30,)
    DAYS_IN_MONTHS_365 = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    DAYS_IN_MONTHS_366 = (31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

    # {mode: (days_in_months, days_in_months_leap), ...}
    MODES = {
        MODE_360: (DAYS_IN_MONTHS_360, None),
        MODE_360_DAY: (DAYS_IN_MONTHS_360, None),
        MODE_365: (DAYS_IN_MONTHS_365, None),
        MODE_365_DAY: (DAYS_IN_MONTHS_365, None),
        MODE_366: (DAYS_IN_MONTHS_366, None),
        MODE_366_DAY: (DAYS_IN_MONTHS_366, None),
        MODE_GREGORIAN: (DAYS_IN_MONTHS_365, DAYS_IN_MONTHS_366),
    }

    WEEK_DAY_START_REFERENCE = {"calendar": (2000, 1, 3),
                                "ordinal": (2000, 3)}
    UNIX_EPOCH_DATE_TIME_REFERENCE_PROPERTIES = {
        "year": 1970, "time_zone_hour": 0, "time_zone_minute": 0}

    _DEFAULT = None

    @classmethod
    def default(cls):
        """Return the singleton instance. Create if necessary."""
        if cls._DEFAULT is None:
            cls._DEFAULT = cls()
        return cls._DEFAULT

    def __init__(self):
        self.set_mode()

    def set_mode(self, mode=None):
        """Set calendar mode.

        mode -- calendar mode, which can be one of the keys in Calendar.MODES.
                If None, default to MODE_GREGORIAN.

        """
        if not mode:
            mode = self.MODE_GREGORIAN
        days_in_months, days_in_months_leap = self.MODES[mode.lower()]
        if days_in_months_leap is None:
            days_in_months_leap = days_in_months
        self.DAYS_IN_MONTHS = days_in_months
        self.DAYS_IN_MONTHS_LEAP = days_in_months_leap
        self.mode = mode

        # Recalculate
        self.SECONDS_IN_HOUR = self.SECONDS_IN_MINUTE * self.MINUTES_IN_HOUR
        self.SECONDS_IN_DAY = self.SECONDS_IN_HOUR * self.HOURS_IN_DAY
        self.MINUTES_IN_DAY = self.MINUTES_IN_HOUR * self.HOURS_IN_DAY
        self.INDEXED_DAYS_IN_MONTHS = [
            (i + 1, days) for i, days in enumerate(self.DAYS_IN_MONTHS)]
        self.INDEXED_DAYS_IN_MONTHS_LEAP = [
            (i + 1, days) for i, days in enumerate(self.DAYS_IN_MONTHS_LEAP)]
        self.REVERSED_INDEXED_DAYS_IN_MONTHS = (
            reversed(self.INDEXED_DAYS_IN_MONTHS))
        self.REVERSED_INDEXED_DAYS_IN_MONTHS_LEAP = (
            reversed(self.INDEXED_DAYS_IN_MONTHS))
        self.MONTHS_IN_YEAR = len(self.DAYS_IN_MONTHS)
        # No support for MONTHS_IN_YEAR_LEAP (some calendars...)
        self.DAYS_IN_YEAR = sum(self.DAYS_IN_MONTHS)
        self.ROUGH_DAYS_IN_YEAR = self.DAYS_IN_YEAR
        self.DAYS_IN_YEAR_LEAP = sum(self.DAYS_IN_MONTHS_LEAP)
        self.MAX_DAYS_IN_MONTH = max(self.DAYS_IN_MONTHS)
        self.HOURS_IN_YEAR = self.DAYS_IN_YEAR * self.HOURS_IN_DAY
        self.MINUTES_IN_YEAR = self.DAYS_IN_YEAR * self.MINUTES_IN_DAY
        self.SECONDS_IN_YEAR = self.DAYS_IN_YEAR * self.SECONDS_IN_DAY
        self.HOURS_IN_YEAR_LEAP = self.DAYS_IN_YEAR_LEAP * self.HOURS_IN_DAY
        self.MINUTES_IN_YEAR_LEAP = (
            self.DAYS_IN_YEAR_LEAP * self.MINUTES_IN_DAY)
        self.SECONDS_IN_YEAR_LEAP = (
            self.DAYS_IN_YEAR_LEAP * self.SECONDS_IN_DAY)

    def __repr__(self):
        return "<{0}.{1}: {2}>".format(
            self.__module__, self.__class__.__name__, self.mode)


CALENDAR = Calendar.default()


TIMEPOINT_DUMPER_MAP = {
    0: dumpers.TimePointDumper(num_expanded_year_digits=0),
    2: dumpers.TimePointDumper(num_expanded_year_digits=2)
}


class TimeRecurrence:

    """Represent a recurring duration.

    There are four possible formats for recurrences in ISO 8601:
    1. Recur with a duration given by the difference between a start date-time
        and a subsequent date-time.
    2. (Not supported) Recur with a specified duration, starting at some
        context date-time specified elsewhere.
    3. Recur with a specified duration starting at a particular date-time.
    4. Recur with a specified duration ending at a particular date-time (the
        starting date-time is calculated from the duration).

    The format of the TimeRecurrence instance is automatically chosen from the
    arguments supplied.

    Keyword arguments:

    repetitions (int): The number of repetitions in the recurrence. If set
        to 1, the recurrence simply consists of one date-time, with no
        duration (i.e., the number of repetitions is inclusive of the first
        occurrence). If omitted, the number of repetitions is unbounded.
    start_point (TimePoint): Start date-time of the recurrence.
    duration (Duration): The duration of each repetition interval in the
        recurrence.
    end_point (TimePoint): End date-time of the recurrence (format 4), or if
        using format 1, the end date-time of the first interval.
    min_point (TimePoint): If specified, marks the start of a subset of 'valid'
        date-times in the recurrence.
    max_point (TimePoint): If specified, marks the end of a subset of 'valid'
        date-times in the recurrence.
    """

    __slots__ = ["_repetitions", "_start_point", "_duration", "_end_point",
                 "_second_point", "_format_number", "_min_point", "_max_point"]

    def __init__(self, repetitions=None, start_point=None,
                 duration=None, end_point=None, min_point=None,
                 max_point=None):
        inputs = (
            (repetitions, "repetitions", None, int),
            (start_point, "start_point", None, TimePoint),
            (duration, "duration", None, Duration),
            (end_point, "end_point", None, TimePoint),
            (min_point, "min_point", None, TimePoint),
            (max_point, "max_point", None, TimePoint)
        )
        _type_checker(*inputs)
        self._repetitions = repetitions
        self._start_point = start_point
        self._duration = duration
        self._end_point = end_point
        self._min_point = min_point
        self._max_point = max_point
        self._format_number = None
        if self._repetitions is not None and self._repetitions <= 0:
            raise BadInputError(BadInputError.RECURRENCE,
                                "Number of repetitions cannot be <= 0")
        if self._duration is not None and self._duration < Duration(years=0):
            raise BadInputError(BadInputError.RECURRENCE,
                                "Duration cannot be < P0Y")
        if self._duration is None:
            # First form.
            self._format_number = 1
            # One repetition means the event only occurs on the start date
            if self._repetitions == 1:
                self._second_point = self._end_point = self._start_point
                return
            if self._start_point is None or self._end_point is None:
                raise BadInputError(
                    BadInputError.RECURRENCE, [i[:2] for i in inputs])
            if self._start_point == self._end_point:
                self._repetitions = 1
                self._second_point = self._end_point
                return
            if self._end_point < self._start_point:
                raise BadInputError(
                    BadInputError.RECURRENCE, "Start point {0} cannot be "
                    "earlier than end point of first interval {1}"
                    .format(self._start_point, self._end_point))
            self._second_point = self._end_point
            self._duration = self._second_point - self._start_point
            if self._repetitions is None:
                self._end_point = None
            else:
                self._end_point = (
                    self._start_point +
                    self._duration * (self._repetitions - 1))
        elif self._end_point is None and self._start_point is not None:
            # Third form.
            self._format_number = 3
            if self._repetitions == 1 or self._duration == Duration(years=0):
                self._end_point = self._start_point
                self._repetitions = 1
                self._duration = None
            elif self._repetitions is not None:
                self._end_point = (
                    self._start_point +
                    self._duration * (self._repetitions - 1))
        elif self._start_point is None and self._end_point is not None:
            # Fourth form.
            self._format_number = 4
            if self._repetitions == 1 or self._duration == Duration(years=0):
                self._start_point = self._end_point
                self._repetitions = 1
                self._duration = None
            elif self._repetitions is not None:
                self._start_point = (
                    self._end_point - self._duration * (self._repetitions - 1))
        else:
            raise BadInputError(
                BadInputError.RECURRENCE, [i[:2] for i in inputs])

    @property
    def repetitions(self): return self._repetitions

    @property
    def start_point(self): return self._start_point

    @property
    def duration(self): return self._duration

    @property
    def end_point(self): return self._end_point

    @property
    def min_point(self): return self._min_point

    @property
    def max_point(self): return self._max_point

    @property
    def format_number(self): return self._format_number

    def get_is_valid(self, timepoint: "TimePoint") -> bool:
        """Return whether the timepoint is valid for this recurrence."""
        if not self._get_is_in_bounds(timepoint):
            return False
        for iter_timepoint in self.__iter__():
            if iter_timepoint == timepoint:
                return True
            if self._start_point is None and iter_timepoint < timepoint:
                return False
            if self._end_point is None and iter_timepoint > timepoint:
                return False
        return False

    def get_next(self, timepoint: "TimePoint") -> "TimePoint":
        """Return the next timepoint after this timepoint in the recurrence
        series, or None."""
        if self._repetitions == 1 or timepoint is None:
            return None
        next_timepoint = timepoint + self._duration
        if self._get_is_in_bounds(next_timepoint):
            return next_timepoint
        return None

    def get_prev(self, timepoint: "TimePoint") -> "TimePoint":
        """Return the previous timepoint before this timepoint in the
        recurrence series, or None."""
        if self._repetitions == 1 or timepoint is None:
            return None
        prev_timepoint = timepoint - self._duration
        if self._get_is_in_bounds(prev_timepoint):
            return prev_timepoint
        return None

    def __getitem__(self, index: int) -> "TimePoint":
        if index < 0 or not isinstance(index, int):
            raise IndexError("Unsupported index for TimeRecurrence")
        for i, point in enumerate(self.__iter__()):
            if index == i:
                return point
        raise IndexError("Invalid index for TimeRecurrence")

    def _get_is_in_bounds(self, timepoint: "TimePoint") -> bool:
        """Return whether the timepoint is within this recurrence series."""
        if timepoint is None:
            return False
        if self._start_point is not None and timepoint < self._start_point:
            return False
        if self._min_point is not None and timepoint < self._min_point:
            return False
        if self._max_point is not None and timepoint > self._max_point:
            return False
        if self._end_point is not None and timepoint > self._end_point:
            return False
        return True

    def __iter__(self):
        if self._start_point is None:
            point = self._end_point
            in_reverse = True
        else:
            point = self._start_point
            in_reverse = False

        if self._repetitions == 1 or not self._duration:
            if self._get_is_in_bounds(point):
                yield point
            point = None

        while point is not None:
            if self._get_is_in_bounds(point):
                yield point
            else:
                break
            if in_reverse:
                point = self.get_prev(point)
            else:
                point = self.get_next(point)

    def __hash__(self) -> int:
        return hash((self._repetitions, self._start_point, self._end_point,
                     self._duration, self._min_point, self._max_point))

    def __eq__(self, other: "TimeRecurrence") -> bool:
        if not isinstance(other, TimeRecurrence):
            return NotImplemented
        for attr in ["_repetitions", "_start_point", "_end_point", "_duration",
                     "_min_point", "_max_point"]:
            if getattr(self, attr) != getattr(other, attr):
                return False
        return True

    def __add__(self, other: "Duration") -> "TimeRecurrence":
        if not isinstance(other, Duration):
            raise TypeError(
                "Invalid type for addition: '{0}' should be Duration."
                .format(type(other).__name__)
            )
        if self._format_number == 1:
            kwargs = {"start_point": self._start_point + other,
                      "end_point": self._second_point + other}
        elif self._format_number == 3:
            kwargs = {"start_point": self._start_point + other,
                      "duration": self._duration}
        elif self._format_number == 4:
            kwargs = {"end_point": self._end_point + other,
                      "duration": self._duration}
        return self.__class__(
            repetitions=self._repetitions, **kwargs,
            min_point=self._min_point, max_point=self._max_point)

    def __sub__(self, other: "Duration") -> "TimeRecurrence":
        return self + -1 * other

    def __str__(self):
        if self._repetitions is None:
            prefix = "R/"
        else:
            prefix = "R" + str(self._repetitions) + "/"
        duration_str = (
            str(self._duration) if self._duration is not None else 'P0Y')
        if self._format_number == 1:
            return (prefix + str(self._start_point) + "/" +
                    str(self._second_point))
        elif self._format_number == 3:
            return prefix + str(self._start_point) + "/" + duration_str
        elif self._format_number == 4:
            return prefix + duration_str + "/" + str(self._end_point)
        return "R/?/?"

    def __repr__(self):
        return "<{0}.{1}: {2}>".format(
            self.__module__, self.__class__.__name__, str(self))


class Duration:

    """Represent a duration or period of time.

    Note that years and months are 'nominal' durations, whose exact length of
    time depends on their position in the calendar. E.g., a duration of
    1 calendar year starts on a particular day of a particular month and ends
    on the same day of the same month in the following calendar year, and may
    be different to 365 days in the Gregorian calendar due to leap years.

    For this reason, be careful when using the comparison operators. For the
    sake of `<`, `<=`, `>` and `>=`, the behaviour is: P1Y = P365D and
    P1M = P30D. However, these are not NOT true for the equality operator
    (`==`).

    Conversely, weeks, days, hours, minutes and seconds are exact units, so
    P1W == P7D, P1D == PT24H and PT1H == PT60M etc. are always true. (Although
    ISO 8601 states that weeks and days are nominal durations, there is no case
    where they are not exact in our implementation.)

    Keyword arguments:

    years (int): number of calendar years in the duration (an inexact unit
        due to the possibility of leap years).
    months (int) number of calendar months in the duration (also an inexact
        unit due to the differing number of calendar days in the calendar
        months).
    weeks (int): number of calendar weeks in the duration - cannot be used in
        conjunction with other units (use multiples of 7 days instead).
    days (int): number of calendar days in the duration.
    hours (float): number of hours in the duration.
    minutes (float): number of minutes in the duration.
    seconds (float): number of seconds in the duration.
    standardize (bool): if True, switches on adjusting the attributes so that
        small units have minimal values. For example, 3664.4 seconds would
        become 1 hour, 1 minute, and 4.4 seconds. Attributes will not adjust
        for units that are inexact (months and years).
    _is_empty_instance (bool): If True, do not set any properties yet. These
        should be set as part of a copy operation.
    """

    __slots__ = ["_years", "_months", "_weeks", "_days",
                 "_hours", "_minutes", "_seconds"]

    def __init__(self, years=0, months=0, weeks=0, days=0,
                 hours=0.0, minutes=0.0, seconds=0.0, standardize=False,
                 _is_empty_instance=False):
        if _is_empty_instance:
            return
        _type_checker(
            (years, "years", int, None),
            (months, "months", int, None),
            (weeks, "weeks", int, None),
            (days, "days", int, None),
            (hours, "hours", int, float, None),
            (minutes, "minutes", int, float, None),
            (seconds, "seconds", int, float, None)
        )
        self._years = years
        self._months = months
        self._weeks = None
        self._days = days
        if weeks is not None:
            if days is None:
                self._days = CALENDAR.DAYS_IN_WEEK * weeks
            else:
                self._days += CALENDAR.DAYS_IN_WEEK * weeks
        self._hours = hours
        self._minutes = minutes
        self._seconds = seconds
        if (weeks and not years and not months and not days and
                not hours and not minutes and not seconds):
            self._weeks = self._days // CALENDAR.DAYS_IN_WEEK
            self._years, self._months, self._days = (None, None, None)
            self._hours, self._minutes, self._seconds = (None, None, None)
        if standardize:
            if self._seconds:
                num_minutes, self._seconds = divmod(
                    self._seconds, CALENDAR.SECONDS_IN_MINUTE)
                if self._minutes is None:
                    self._minutes = 0
                self._minutes += num_minutes
            if self._minutes:
                num_hours, self._minutes = divmod(
                    self._minutes, CALENDAR.MINUTES_IN_HOUR)
                if self._hours is None:
                    self._hours = 0
                self._hours += num_hours
            if self._hours:
                num_days, self._hours = divmod(
                    self._hours, CALENDAR.HOURS_IN_DAY)
                if self._days is None:
                    self._days = 0
                self._days += num_days

    @property
    def years(self): return self._years

    @property
    def months(self): return self._months

    @property
    def weeks(self): return self._weeks

    @property
    def days(self): return self._days

    @property
    def hours(self): return self._hours

    @property
    def minutes(self): return self._minutes

    @property
    def seconds(self): return self._seconds

    def _copy(self):
        """Return an (unlinked) copy of this instance."""
        new = self.__class__(_is_empty_instance=True)
        for attr in self.__slots__:
            setattr(new, attr, getattr(self, attr))
        return new

    def is_exact(self):
        """Return True if the instance is defined in non-nominal/exact units
        (weeks, days, hours, minutes or seconds) only."""
        if self._years or self._months:
            return False
        return True

    def get_days_and_seconds(self):
        """Return a roughly-converted duration in days and seconds.

        This cannot be accurate for non-uniform units such as years and
        months, and may yield incorrect results if used for comparisons
        derived from durations using these units.

        Seconds are returned in the range
        0 <= seconds < CALENDAR.SECONDS_IN_DAY, which means that a
        Duration which has self.seconds = CALENDAR.SECONDS_IN_DAY +
        100 will return 1 day, 100 seconds or (1, 100) from this
        method.
        """
        if self.get_is_in_weeks():
            return self._weeks * CALENDAR.DAYS_IN_WEEK, 0
        # TODO: Implement error calculation for the below quantities.
        new_days = (self._years * CALENDAR.ROUGH_DAYS_IN_YEAR +
                    self._months * CALENDAR.ROUGH_DAYS_IN_MONTH +
                    self._days)
        new_seconds = (self._hours * CALENDAR.SECONDS_IN_HOUR +
                       self._minutes * CALENDAR.SECONDS_IN_MINUTE +
                       self._seconds)
        diff_days, new_seconds = divmod(new_seconds, CALENDAR.SECONDS_IN_DAY)
        new_days += diff_days
        return new_days, new_seconds

    def get_seconds(self):
        """Return a roughly-converted duration in seconds.

        This is not rigorous when converting from non-uniform units
        such as years and months.
        """
        if self.is_exact():
            return self._get_non_nominal_seconds()
        days, seconds = self.get_days_and_seconds()
        return days * CALENDAR.SECONDS_IN_DAY + seconds

    def _get_non_nominal_seconds(self):
        """Return the length of time (in seconds) represented by the exact
        units (weeks, days, hours, minutes and seconds) only, ignoring
        years and months."""
        if self.get_is_in_weeks():
            return (self._weeks * CALENDAR.DAYS_IN_WEEK *
                    CALENDAR.SECONDS_IN_DAY)
        return (self._days * CALENDAR.SECONDS_IN_DAY +
                self._hours * CALENDAR.SECONDS_IN_HOUR +
                self._minutes * CALENDAR.SECONDS_IN_MINUTE + self._seconds)

    def get_is_in_weeks(self):
        """Return whether we are in week representation."""
        return self._weeks is not None

    def to_days(self):
        """Return a new Duration in day representation rather than weeks."""
        if self.get_is_in_weeks():
            new = self._copy()
            for attribute in ["_years", "_months", "_hours",
                              "_minutes", "_seconds"]:
                if getattr(new, attribute) is None:
                    setattr(new, attribute, 0)
            new._days = new._weeks * CALENDAR.DAYS_IN_WEEK
            new._weeks = None
            return new
        return self

    def to_weeks(self):
        """Return a new Duration in week representation (use with caution -
        this returns the floor of the decimal number of weeks, so might lose
        precision)."""
        if not self.get_is_in_weeks():
            weeks = self._days // CALENDAR.DAYS_IN_WEEK
            return Duration(weeks=weeks)
        return self

    def __abs__(self):
        new = self._copy()
        for attribute in new.__slots__:
            attr_value = getattr(new, attribute)
            if attr_value is not None:
                setattr(new, attribute, abs(attr_value))
        return new

    def __add__(self, other):
        new = self._copy()
        if isinstance(other, Duration):
            if new.get_is_in_weeks():
                if other.get_is_in_weeks():
                    new._weeks += other._weeks
                    return new
                new = new.to_days()
            elif other.get_is_in_weeks():
                other = other.to_days()
            new._years += other._years
            new._months += other._months
            new._days += other._days
            new._hours += other._hours
            new._minutes += other._minutes
            new._seconds += other._seconds
            return new
        if isinstance(other, TimePoint) or isinstance(other, TimeRecurrence):
            return other + new
        raise TypeError(
            "Invalid type for addition: " +
            "'%s' should be Duration or TimePoint." %
            type(other).__name__
        )

    def __sub__(self, other):
        return self + -1 * other

    def __mul__(self, other):
        # TODO: support float multiplication?
        if not isinstance(other, int):
            raise TypeError(
                "Invalid type for multiplication: " +
                "'%s' should be integer." %
                type(other).__name__
            )
        new = self._copy()
        for attr in new.__slots__:
            value = getattr(new, attr)
            if value is not None:
                setattr(new, attr, value * other)
        return new

    def __rmul__(self, other):
        return self.__mul__(other)

    def __floordiv__(self, other):
        # TODO: support float division?
        if not isinstance(other, int):
            raise TypeError(
                "Invalid type for division: " +
                "'%s' should be integer." %
                type(other).__name__
            )
        new = self._copy()
        if self.get_is_in_weeks():
            new._weeks //= other
            return new
        new._years //= other
        new._months //= other
        new._days //= other
        new._hours //= other
        new._minutes //= other
        new._seconds //= other
        return new

    def __hash__(self) -> int:
        # TODO: alt calendar modes
        if self.get_is_in_weeks():
            return hash((0, 0, self._get_non_nominal_seconds()))
        return hash(
            (self._years, self._months, self._get_non_nominal_seconds()))

    def __eq__(self, other: "Duration") -> bool:
        if isinstance(other, Duration):
            if self.is_exact():
                if other.is_exact():
                    return (self._get_non_nominal_seconds() ==
                            other._get_non_nominal_seconds())
                return False
            return (
                self._years == other._years and
                self._months == other._months and
                self._get_non_nominal_seconds() ==
                other._get_non_nominal_seconds()
            )
        return NotImplemented

    def __lt__(self, other: "Duration") -> bool:
        if isinstance(other, Duration):
            return self.get_days_and_seconds() < other.get_days_and_seconds()
        return NotImplemented

    def __le__(self, other: "Duration") -> bool:
        if isinstance(other, Duration):
            return self.get_days_and_seconds() <= other.get_days_and_seconds()
        return NotImplemented

    def __gt__(self, other: "Duration") -> bool:
        if isinstance(other, Duration):
            return self.get_days_and_seconds() > other.get_days_and_seconds()
        return NotImplemented

    def __ge__(self, other: "Duration") -> bool:
        if isinstance(other, Duration):
            return self.get_days_and_seconds() >= other.get_days_and_seconds()
        return NotImplemented

    def __bool__(self):
        for attr in self.__slots__:
            if getattr(self, attr, None):
                return True
        return False

    def __str__(self):
        if not self:
            return "P0Y"

        start_string = "P"
        content_string = ""

        # Handle negative durations.
        is_fully_negative = False
        for attribute in self.__slots__:
            attr_value = getattr(self, attribute)
            if attr_value is not None:
                if attr_value > 0:
                    is_fully_negative = False
                    break
                if attr_value < 0:
                    is_fully_negative = True
        if is_fully_negative:
            # Support negative durations as extensions to the standard.
            return "-" + str(abs(self))

        # Weeks are not combined with any other unit.
        if self.get_is_in_weeks():
            return (start_string + str(self._weeks) + "W").replace(".", ",")

        for prop_, unit in [("years", "Y"), ("months", "M"), ("days", "D"),
                            ("hours", "H"), ("minutes", "M"),
                            ("seconds", "S")]:
            prop_val = getattr(self, prop_)
            if prop_val:
                if int(prop_val) == prop_val:
                    content_string += str(int(prop_val)) + unit
                else:
                    content_string += str(prop_val) + unit
            if prop_ == "days":
                content_string += "T"

        if content_string.endswith("T"):
            # No time unit information, so strip the delimiter.
            content_string = content_string[:-1]

        total_string = start_string + content_string
        return total_string.replace(".", ",")

    def __repr__(self):
        return "<{0}.{1}: {2}>".format(
            self.__module__, self.__class__.__name__, str(self))


class TimeZone(Duration):

    """Represent a time zone offset from UTC.

    Keyword arguments:

    hours (int): The hour component of the offset from UTC. May be positive,
        zero, or negative, as required.
    minutes (int): The minute component offset from UTC. If the UTC offset is
        negative, this should be negative if non-zero.
    unknown (bool): If True, the returned instance represents an unknown
        TimeZone. Some operations and comparisons may fail when this is True.
    _is_empty_instance (bool): If True, do not set any properties yet. These
        should be set as part of a copy operation.
    """

    __slots__ = [*Duration.__slots__, "_unknown"]

    to_weeks = property(doc='Unavailable/not inherited')

    def __init__(self, hours=0, minutes=0, unknown=False,
                 _is_empty_instance=False):
        if _is_empty_instance:
            return
        if hours is None:
            hours = 0
        else:
            hours = _int_caster(hours, "TimeZone hours")
            _bounds_checker(hours, "TimeZone hours",
                            min_val=-99, max_val=99)
        if minutes is None:
            minutes = 0
        else:
            minutes = _int_caster(minutes, "TimeZone minutes")
            min_minutes = 1 - CALENDAR.MINUTES_IN_HOUR
            max_minutes = CALENDAR.MINUTES_IN_HOUR - 1
            if hours > 0:
                min_minutes = 0
            elif hours < 0:
                max_minutes = 0
            _bounds_checker(minutes, "TimeZone minutes",
                            min_val=min_minutes, max_val=max_minutes)
        self._unknown = unknown
        self._hours = hours
        self._minutes = minutes
        for attr in ["_years", "_months", "_days", "_seconds"]:
            setattr(self, attr, 0)
        self._weeks = None

    @property
    def unknown(self): return self._unknown

    def __hash__(self) -> int:
        # TODO: Do we have to worry about the possibility of a hash collision
        # between instances of two different classes?
        return hash((self._unknown, self._hours, self._minutes))

    def __str__(self):
        if self._unknown:
            return ""
        if self._hours == 0 and self._minutes == 0:
            return "Z"
        else:
            time_string = "+%02d:%02d"
            if self._hours < 0 or (self._hours == 0 and self._minutes < 0):
                time_string = "-%02d:%02d"
            return time_string % (abs(self._hours), abs(self._minutes))


class TimePoint:

    """Represent an instant in time.

    An ISO 8601 date/time instant can be represented in three separate ways:
    - Calendar date: calendar year, calendar month, calendar day of the month
    - Ordinal date: calendar year, calendar day of the year
    - Week date: calendar (week) year, calendar week, calendar day of the week
      (note: week years are not identical to calendar years).

    This class maintains a date/time instant in the original
    representation with which it was invoked - so it may be in any of
    these formats. See the TimePoint.to_*_date methods for internal
    conversions between formats.

    Where properties are not given (consistent with ISO 8601 reduced
    precision dates), they will be given the expected defaults if
    truncation is not specified. For example, if only the year and the
    month_of_year is given, the day_of_month will be set to 1.

    Time zone information defaults to UTC. It is essential to provide it
    unless you are happy with this behaviour. A date/time
    representation is ambiguous without it.

    Keyword arguments (usually default to None if not provided):

    num_expanded_year_digits (default 0) - an agreed-upon number of extra
        digits to represent the year, beyond the normal 4. For example,
        a value of 2 would suggest representing the year 2000 as 002000.
    year (int): A positive or negative integer. Note that ISO 8601 implies
        using non-zero num_expanded_year_digits when using negative integers.
        Remember we are using the proleptic Gregorian calendar, with a year
        zero which does not exist in standard 1 BC => 1 AD usage - so 2 BC
        should be represented as -1.
    month_of_year (int): An integer between 1 and 12 inclusive, if using the
        calendar date representation.
    week_of_year (int): An integer between 1 and 52/53 (depending on the
        year), if using the week date representation.
    day_of_year (int): An integer between 1 and 365/366 (depending on the
        year), if using the ordinal date representation.
    day_of_month (int): An integer between 1 and 28/29/30/31 (depending on
        the month and year), if using the calendar date representation.
    day_of_week (int): An integer between 1 and 7, if using the week date
        representation.
    hour_of_day (int): An integer between 0 and 24 (note: 24 represents
        midnight at the end of the day, which is equivalent to 00/midnight
        the next day. If 24 is given, minute_of_hour must be 0).
    hour_of_day_decimal (float): A float between 0 and 1, if using decimal
        accuracy for hours. Note that you should not provide lower units
        such as minute_of_hour or second_of_minute when using this.
    minute_of_hour (int): An integer between 0 and 59.
    minute_of_hour_decimal (float): A float between 0 and 1, if using decimal
        accuracy for minutes. Note that you should not provide lower units
        such as second_of_minute when using this.
    second_of_minute (int): An integer between 0 and 59 (note: no support
        for leap seconds yet).
    second_of_minute_decimal (float): A float between 0 and 1, if using decimal
        accuracy for seconds.
    time_zone_hour (int): The hour component of the time zone offset from UTC,
        between -99 and 99. The default is 0 unless this is a truncated
        TimePoint.
    time_zone_minute (int): The minute component of the time zone offset from
        UTC. If the hour component is negative, this should be negative too.
    dump_format (str): A custom format string to control the stringification
        of the timepoint. See isodatetime.parser_spec for more details.
    truncated (bool): Whether the date-time instant has purposefully incomplete
        information (ISO 8601:2000 truncation). Default is False.
    truncated_dump_format (str): A custom format to control the stringification
        of the timepoint if it is truncated. See isodatetime.parser_spec for
        more details.
    truncated_property (str): Can either be "year_of_decade" or
        "year_of_century". This is used for truncated representations to
        distinguish between the two ways of truncating the year.
    is_empty_instance (bool): If True, do not set any properties yet. These
        should be set as part of a copy operation. Default is False.
    is_duration (bool): For datetime-like durations syntax. If True the
        args will not be checked to make sure values are within bounds, and if
        the values of month_of_year, day_of_month etc are not supplied they
        will be assumed to be 0 instead of 1. Default is False.
    """

    __slots__ = [
        "_num_expanded_year_digits", "_year", "_month_of_year",
        "_day_of_year", "_day_of_month", "_day_of_week",
        "_week_of_year", "_hour_of_day", "_minute_of_hour",
        "_second_of_minute", "_truncated", "_truncated_property",
        "_truncated_dump_format", "_dump_format", "_time_zone"
    ]

    def __init__(self, num_expanded_year_digits=0, year=None,
                 month_of_year=None, week_of_year=None, day_of_year=None,
                 day_of_month=None, day_of_week=None,
                 hour_of_day=None, hour_of_day_decimal=None,
                 minute_of_hour=None, minute_of_hour_decimal=None,
                 second_of_minute=None, second_of_minute_decimal=None,
                 time_zone_hour=None, time_zone_minute=None,
                 dump_format=None, truncated=False,
                 truncated_dump_format=None, truncated_property=None,
                 is_empty_instance=False, is_duration=False):
        if is_empty_instance:
            # This has been created for a copy - set properties later.
            return
        if dump_format is not None and not isinstance(dump_format, str):
            raise BadInputError(
                BadInputError.TYPE,
                "dump_format", repr(dump_format), type(dump_format))
        if (truncated_dump_format is not None and
                not isinstance(truncated_dump_format, str)):
            raise BadInputError(
                BadInputError.TYPE,
                "truncated_dump_format", repr(truncated_dump_format),
                type(truncated_dump_format)
            )
        if (truncated_property is not None and
                truncated_property not in ["year_of_decade",
                                           "year_of_century"]):
            raise BadInputError(
                BadInputError.VALUES, "truncated_property",
                repr(truncated_property),
                "'year_of_decade' or 'year_of_century'")
        _type_checker(
            (num_expanded_year_digits, "num_expanded_year_digits", int),
            (year, "year", None, int),
            (month_of_year, "month_of_year", None, int),
            (week_of_year, "week_of_year", None, int),
            (day_of_year, "day_of_year", None, int),
            (day_of_month, "day_of_month", None, int),
            (day_of_week, "day_of_week", None, int),
            (hour_of_day, "hour_of_day", None, int, float),
            (hour_of_day_decimal, "hour_of_day_decimal", None, int, float),
            (minute_of_hour, "minute_of_hour", None, int, float),
            (minute_of_hour_decimal, "minute_of_hour_decimal", None, int,
             float),
            (second_of_minute, "second_of_minute", None, int, float),
            (second_of_minute_decimal, "second_of_minute_decimal", None, int,
             float)
        )
        self._dump_format = dump_format
        self._num_expanded_year_digits = _int_caster(
            num_expanded_year_digits, "num_expanded_year_digits")
        self._truncated = truncated
        self._truncated_dump_format = truncated_dump_format
        self._truncated_property = truncated_property

        self._year = _int_caster(year, "year", allow_none=True)
        self._month_of_year = _int_caster(month_of_year, "year",
                                          allow_none=True)
        self._day_of_year = _int_caster(day_of_year, "day_of_year",
                                        allow_none=True)
        self._day_of_month = _int_caster(day_of_month, "day_of_month",
                                         allow_none=True)
        self._day_of_week = _int_caster(day_of_week, "day_of_week",
                                        allow_none=True)
        self._week_of_year = _int_caster(week_of_year, "week_of_year",
                                         allow_none=True)
        self._hour_of_day = _int_caster(hour_of_day, "hour_of_day",
                                        allow_none=True)
        if hour_of_day_decimal is not None:
            if self._hour_of_day is None:
                raise BadInputError(
                    BadInputError.MISSING, "hour_of_day_decimal",
                    "hour_of_day")
            hour_of_day_decimal = float(hour_of_day_decimal)
            _bounds_checker(hour_of_day_decimal, "hour_of_day_decimal",
                            min_val=0, upper_val=1)
            self._hour_of_day += hour_of_day_decimal
            if minute_of_hour is not None:
                raise BadInputError(
                    BadInputError.CONFLICT, "minute_of_hour",
                    "hour_of_day_decimal")
            if second_of_minute is not None:
                raise BadInputError(
                    BadInputError.CONFLICT, "second_of_minute",
                    "hour_of_day_decimal")
        if minute_of_hour_decimal is not None:
            if minute_of_hour is None:
                raise BadInputError(
                    BadInputError.MISSING, "minute_of_hour_decimal",
                    "minute_of_hour")
            self._minute_of_hour = _int_caster(
                minute_of_hour, "minute_of_hour")
            minute_of_hour_decimal = float(minute_of_hour_decimal)
            _bounds_checker(minute_of_hour_decimal, "minute_of_hour_decimal",
                            min_val=0, upper_val=1)
            self._minute_of_hour += minute_of_hour_decimal
            if second_of_minute is not None:
                raise BadInputError(
                    BadInputError.CONFLICT, "second_of_minute",
                    "minute_of_hour_decimal")
        else:
            self._minute_of_hour = _int_caster(
                minute_of_hour, "minute_of_hour", allow_none=True)
        if second_of_minute_decimal is not None:
            if second_of_minute is None:
                raise BadInputError(
                    BadInputError.MISSING,
                    "second_of_minute_decimal",
                    "second_of_minute")
            self._second_of_minute = _int_caster(second_of_minute,
                                                 "second_of_minute")
            second_of_minute_decimal = float(second_of_minute_decimal)
            _bounds_checker(second_of_minute_decimal,
                            "second_of_minute_decimal", min_val=0, upper_val=1)
            self._second_of_minute += second_of_minute_decimal
        else:
            self._second_of_minute = _int_caster(
                second_of_minute, "second_of_minute", allow_none=True)
        if not self._truncated:
            if self._year is None:
                raise BadInputError("Missing input: year")
            if self._hour_of_day is None:
                self._hour_of_day = 0
            if hour_of_day_decimal is None and self._minute_of_hour is None:
                self._minute_of_hour = 0
            if (hour_of_day_decimal is None and
                    minute_of_hour_decimal is None and
                    self._second_of_minute is None):
                self._second_of_minute = 0

        has_unknown_tz = self._truncated and not (
            time_zone_hour is not None or time_zone_minute is not None)
        self._time_zone = TimeZone(hours=time_zone_hour,
                                   minutes=time_zone_minute,
                                   unknown=has_unknown_tz)

        month_is_specified = bool(self._month_of_year or self._day_of_month)
        week_is_specified = bool(self._week_of_year or self._day_of_week)
        if month_is_specified and week_is_specified:
            raise BadInputError(BadInputError.CONFLICT,
                                "[week_of_year or day_of_week]",
                                "[month_of_year or day_of_month]")
        if month_is_specified and self._day_of_year is not None:
            raise BadInputError(BadInputError.CONFLICT,
                                "day_of_year",
                                "[month_of_year or day_of_month]")
        if week_is_specified and self._day_of_year is not None:
            raise BadInputError(BadInputError.CONFLICT,
                                "day_of_year",
                                "[week_of_year or day_of_week]")
        if not is_duration:
            if not self._truncated and self._day_of_year is None:
                if not week_is_specified:
                    if self._month_of_year is None:
                        self._month_of_year = 1
                    if self._day_of_month is None:
                        self._day_of_month = 1
                else:
                    if self._week_of_year is None:
                        self._week_of_year = 1
                    if self._day_of_week is None:
                        self._day_of_week = 1
            self._check_bounds()

    @property
    def num_expanded_year_digits(self): return self._num_expanded_year_digits

    @property
    def year(self): return self._year

    @property
    def month_of_year(self):
        if self._month_of_year is None:
            return self.get_calendar_date()[1]
        return self._month_of_year

    @property
    def week_of_year(self):
        if self._week_of_year is None:
            return self.get_week_date()[1]
        return self._week_of_year

    @property
    def day_of_year(self):
        if self._day_of_year is None:
            return self.get_ordinal_date()[1]
        return self._day_of_year

    @property
    def day_of_month(self):
        if self._day_of_month is None:
            return self.get_calendar_date()[2]
        return self._day_of_month

    @property
    def day_of_week(self):
        if self._day_of_week is None:
            return self.get_week_date()[2]
        return self._day_of_week

    @property
    def hour_of_day(self): return self._hour_of_day

    @property
    def minute_of_hour(self):
        if self._minute_of_hour is None:
            return self.get_hour_minute_second()[1]
        return self._minute_of_hour

    @property
    def second_of_minute(self):
        if self._second_of_minute is None:
            return self.get_hour_minute_second()[2]
        return self._second_of_minute

    @property
    def time_zone(self): return self._time_zone
    # NOTE: returns linked instance of TimeZone, but it shouldn't matter
    # because TimeZone is immutable

    @property
    def truncated(self): return self._truncated

    @property
    def truncated_property(self): return self._truncated_property

    @property
    def truncated_dump_format(self): return self._truncated_dump_format

    @property
    def dump_format(self): return self._dump_format

    def get_is_calendar_date(self):
        """Return whether this is in years, month-of-year, day-of-month."""
        return self._month_of_year is not None

    def get_is_ordinal_date(self):
        """Return whether this is in years, day-of-the year format."""
        return self._day_of_year is not None

    def get_is_week_date(self):
        """Return whether this is in years, week-of-year, day-of-week."""
        return self._week_of_year is not None

    def get_calendar_date(self):
        """Return the year, month-of-year and day-of-month for this date."""
        if self.get_is_calendar_date():
            return self._year, self._month_of_year, self._day_of_month
        if self.get_is_ordinal_date():
            return get_calendar_date_from_ordinal_date(self._year,
                                                       self._day_of_year)
        if self.get_is_week_date():
            return get_calendar_date_from_week_date(self._year,
                                                    self._week_of_year,
                                                    self._day_of_week)

    def get_hour_minute_second(self):
        """Return the time of day expressed in hours, minutes, seconds."""
        hour_of_day = self._hour_of_day
        minute_of_hour = self._minute_of_hour
        second_of_minute = self._second_of_minute
        if second_of_minute is None:
            if minute_of_hour is None:
                hour_decimals = hour_of_day - int(hour_of_day)
                hour_of_day = float(int(hour_of_day))
                minute_of_hour = CALENDAR.MINUTES_IN_HOUR * hour_decimals
            minute_decimals = minute_of_hour - int(minute_of_hour)
            minute_of_hour = float(int(minute_of_hour))
            second_of_minute = CALENDAR.SECONDS_IN_MINUTE * minute_decimals
        return hour_of_day, minute_of_hour, second_of_minute

    def get_ordinal_date(self):
        """Return the year, day-of-year for this date."""
        if self.get_is_calendar_date():
            return get_ordinal_date_from_calendar_date(self._year,
                                                       self._month_of_year,
                                                       self._day_of_month)
        if self.get_is_ordinal_date():
            return self._year, self._day_of_year
        if self.get_is_week_date():
            return get_ordinal_date_from_week_date(self._year,
                                                   self._week_of_year,
                                                   self._day_of_week)

    @property
    def year_sign(self): return "+" if self._year >= 0 else "-"

    @property
    def expanded_year_digits(self):
        """The extra digits at the front of the expanded year, as opposed to
        the number of such digits"""
        return abs(self._year / 10000)

    @property
    def century(self): return (abs(self._year) % 10000) // 100

    @property
    def year_of_century(self): return abs(self._year) % 100

    @property
    def year_of_decade(self): return abs(self._year) % 10

    @property
    def decade_of_century(self):
        return (abs(self._year) % 100 - abs(self._year) % 10) // 10

    @property
    def hour_of_day_decimal_string(self):
        return self._decimal_string("hour_of_day")

    @property
    def minute_of_hour_decimal_string(self):
        return self._decimal_string("minute_of_hour")

    @property
    def second_of_minute_decimal_string(self):
        return self._decimal_string("second_of_minute")

    @property
    def time_zone_minute_abs(self): return abs(self._time_zone._minutes)

    @property
    def time_zone_hour_abs(self): return abs(self._time_zone._hours)

    @property
    def time_zone_sign(self):
        if self._time_zone._hours < 0 or self._time_zone._minutes < 0:
            return "-"
        return "+"

    @property
    def seconds_since_unix_epoch(self):
        reference_timepoint = TimePoint(
            **CALENDAR.UNIX_EPOCH_DATE_TIME_REFERENCE_PROPERTIES)
        days, seconds = (self - reference_timepoint).get_days_and_seconds()
        # N.B. This needs altering if we implement leap seconds.
        return str(int(CALENDAR.SECONDS_IN_DAY * days + seconds))

    def get(self, property_name):
        """Obsolete method for returning calculated value for property name."""
        raise NotImplementedError(
            "The method TimePoint.get('{0}') is obsolete; use TimePoint.{0} "
            "or getattr() instead".format(property_name))
        # return getattr(self, property_name)

    def _decimal_string(self, attr):
        """Return the decimal digits (after the decimal point) of the specified
        attribute as a string. Rounds to 6 d.p."""
        decimal = float(getattr(self, attr)) - int(getattr(self, attr))
        if decimal >= 0.9999995:
            # Truncate instead of rounding up because ticking over the higher
            # quantities would be complicated
            return "999999"
        string = "%0.6f" % decimal
        string = string.split(".", 1)[1].rstrip("0")
        if not string:
            return "0"
        return string

    def get_second_of_day(self):
        """Return the seconds elapsed since the start of the day."""
        second_of_day = 0
        if self._second_of_minute is not None:
            second_of_day += self._second_of_minute
        if self._minute_of_hour is not None:
            second_of_day += self._minute_of_hour * CALENDAR.SECONDS_IN_MINUTE
        second_of_day += self._hour_of_day * CALENDAR.SECONDS_IN_HOUR
        return second_of_day

    def get_time_zone_utc(self) -> bool:
        # FIXME: Misleading name
        """Return whether the time zone is explicitly in UTC."""
        if self._time_zone._unknown:
            return False
        return self._time_zone._hours == 0 and self._time_zone._minutes == 0

    def get_week_date(self):
        """Return the year, week-of-year, day-of-week for this date."""
        if self.get_is_calendar_date():
            return get_week_date_from_calendar_date(self._year,
                                                    self._month_of_year,
                                                    self._day_of_month)
        if self.get_is_ordinal_date():
            return get_week_date_from_ordinal_date(self._year,
                                                   self._day_of_year)
        if self.get_is_week_date():
            return self._year, self._week_of_year, self._day_of_week

    def get_time_zone_offset(self, other: "TimePoint") -> "Duration":
        """Get the difference in hours and minutes between time zones.

        Args:
            other (TimePoint): The TimePoint to get the offset with respect to.
        """
        # TODO: unit test?
        if other._time_zone._unknown or self._time_zone._unknown:
            return Duration()
        return other._time_zone - self._time_zone

    def to_time_zone(self, dest_time_zone: "TimeZone") -> "TimePoint":
        """Return a copy of this TimePoint in the specified time zone.

        Args:
            dest_time_zone (TimeZone): The new time zone (a TimeZone instance).
        """
        if dest_time_zone._unknown:
            return self
        new = self + (dest_time_zone - self._time_zone)
        new._time_zone = dest_time_zone
        return new

    def to_local_time_zone(self) -> "TimePoint":
        """Return a copy of this TimePoint in the local time zone."""
        local_hours, local_minutes = timezone.get_local_time_zone()
        return self.to_time_zone(
            TimeZone(hours=local_hours, minutes=local_minutes))

    def to_utc(self) -> "TimePoint":
        """Return a copy of this TimePoint in the UTC time zone."""
        return self.to_time_zone(TimeZone(hours=0, minutes=0))

    def to_calendar_date(self) -> "TimePoint":
        """Return a copy of this TimePoint reformatted in years, month-of-year
        and day-of-month."""
        if self.get_is_calendar_date():
            return self
        new = self._copy()
        new._year, new._month_of_year, new._day_of_month = (
            self.get_calendar_date())
        new._day_of_year = None
        new._week_of_year, new._day_of_week = (None, None)
        return new

    def to_hour_minute_second(self) -> "TimePoint":
        """Return a copy of this TimePoint with any time fractions expanded
        into hours, minutes and seconds."""
        new = self._copy()
        new._hour_of_day, new._minute_of_hour, new._second_of_minute = (
            self.get_hour_minute_second())
        return new

    def to_week_date(self) -> "TimePoint":
        """Return a copy of this TimePoint reformatted in years, week-of-year
        and day-of-week."""
        if self.get_is_week_date():
            return self
        new = self._copy()
        new._year, new._week_of_year, new._day_of_week = self.get_week_date()
        new._day_of_year = None
        new._month_of_year, new._day_of_month = (None, None)
        return new

    def to_ordinal_date(self) -> "TimePoint":
        """Return a copy of this TimePoint reformatted in years and
        day-of-the-year."""
        new = self._copy()
        new._year, new._day_of_year = self.get_ordinal_date()
        new._month_of_year, new._day_of_month = (None, None)
        new._week_of_year, new._day_of_week = (None, None)
        return new

    def get_largest_truncated_property_name(self):
        """Return the largest unit in a truncated representation."""
        if not self._truncated:
            return None
        prop_dict = self.get_truncated_properties()
        for attr in ["year_of_century", "year_of_decade", "month_of_year",
                     "week_of_year", "day_of_year", "day_of_month",
                     "day_of_week", "hour_of_day", "minute_of_hour",
                     "second_of_minute"]:
            if attr in prop_dict:
                return attr
        return None

    def get_smallest_missing_property_name(self):
        """Return the smallest unit missing from a truncated representation."""
        if not self._truncated:
            return None
        prop_dict = self.get_truncated_properties()
        attr_list = (("year_of_century", "century"),
                     ("year_of_decade", "decade_of_century"),
                     ("month_of_year", "year_of_century"),
                     ("week_of_year", "year_of_century"),
                     ("day_of_year", "year_of_century"),
                     ("day_of_month", "month_of_year"),
                     ("day_of_week", "week_of_year"),
                     ("hour_of_day", "day_of_month"),
                     ("minute_of_hour", "hour_of_day"),
                     ("second_of_minute", "minute_of_hour"))
        for attr_key, attr_value in attr_list:
            if attr_key in prop_dict:
                return attr_value
        return None

    def get_truncated_properties(self):
        """Return a map of properties if this is a truncated representation."""
        if not self._truncated:
            return None
        props = {}
        if self._truncated_property == "year_of_decade":
            props.update({"year_of_decade": self._year % 10})
        if self._truncated_property == "year_of_century":
            props.update({"year_of_century": self._year % 100})
        for attr in ["month_of_year", "week_of_year", "day_of_year",
                     "day_of_month", "day_of_week", "hour_of_day",
                     "minute_of_hour", "second_of_minute"]:
            value = getattr(self, "_{0}".format(attr))
            if value is not None:
                props.update({attr: value})
        return props

    def add_truncated(self, year_of_century=None, year_of_decade=None,
                      month_of_year=None, week_of_year=None, day_of_year=None,
                      day_of_month=None, day_of_week=None, hour_of_day=None,
                      minute_of_hour=None, second_of_minute=None):
        """Returns a copy of this TimePoint with truncated time properties
        added to it."""
        new = self._copy()
        if hour_of_day is not None and minute_of_hour is None:
            minute_of_hour = 0
        if ((hour_of_day is not None or minute_of_hour is not None) and
                second_of_minute is None):
            second_of_minute = 0
        if second_of_minute is not None or minute_of_hour is not None:
            new = new.to_hour_minute_second()
        if second_of_minute is not None:
            while new._second_of_minute != second_of_minute:
                new._second_of_minute += 1.0
                new._tick_over()
        if minute_of_hour is not None:
            while new._minute_of_hour != minute_of_hour:
                new._minute_of_hour += 1.0
                new._tick_over()
        if hour_of_day is not None:
            while new._hour_of_day != hour_of_day:
                new._hour_of_day += 1.0
                new._tick_over()
        if day_of_week is not None:
            new = new.to_week_date()
            while new._day_of_week != day_of_week:
                new._day_of_week += 1
                new._tick_over()
        if day_of_month is not None:
            new = new.to_calendar_date()
            while new._day_of_month != day_of_month:
                new._day_of_month += 1
                new._tick_over()
        if day_of_year is not None:
            new = new.to_ordinal_date()
            while new._day_of_year != day_of_year:
                new._day_of_year += 1
                new._tick_over()
        if week_of_year is not None:
            new = new.to_week_date()
            while new._week_of_year != week_of_year:
                new._week_of_year += 1
                new._tick_over()
        if month_of_year is not None:
            new = new.to_calendar_date()
            while new._month_of_year != month_of_year:
                new._month_of_year += 1
                new._tick_over()
        if year_of_decade is not None:
            new = new.to_calendar_date()
            new_year_of_decade = new._year % 10
            while new_year_of_decade != year_of_decade:
                new._year += 1
                new_year_of_decade = new._year % 10
        if year_of_century is not None:
            new = new.to_calendar_date()
            new_year_of_century = new._year % 100
            while new_year_of_century != year_of_century:
                new._year += 1
                new_year_of_century = new._year % 100
        return new

    def __add__(self, other) -> "TimePoint":
        if isinstance(other, TimePoint):
            if self._truncated and not other._truncated:
                new = other.to_time_zone(self._time_zone)
                new = new.add_truncated(**self.get_truncated_properties())
                return new.to_time_zone(other._time_zone)
            if other._truncated and not self._truncated:
                return other + self
        if not isinstance(other, Duration):
            raise ValueError(
                "Invalid addition: can only add Duration or "
                "truncated TimePoint to TimePoint.")
        duration = other
        if duration.get_is_in_weeks():
            duration = duration.to_days()
        new = self._copy()
        if duration._seconds:
            if new._second_of_minute is None:
                if new._minute_of_hour is None:
                    new._hour_of_day += (
                        duration._seconds / float(CALENDAR.SECONDS_IN_HOUR))
                else:
                    new._minute_of_hour += (
                        duration._seconds / float(CALENDAR.SECONDS_IN_MINUTE))
            else:
                new._second_of_minute += duration._seconds
            new._tick_over()
        # FIXME: self._tick_over() broken for truncated TimePoints: issue #168
        if duration._minutes:
            if new._minute_of_hour is None:
                new._hour_of_day += (
                    duration._minutes / float(CALENDAR.MINUTES_IN_HOUR))
            else:
                new._minute_of_hour += duration._minutes
            new._tick_over()
        if duration._hours:
            new._hour_of_day += duration._hours
            new._tick_over()
        if duration._days:
            if new.get_is_calendar_date():
                new._day_of_month += duration._days
            elif new.get_is_ordinal_date():
                new._day_of_year += duration._days
            else:
                new._day_of_week += duration._days
            new._tick_over()
        if duration._months:
            # This is the dangerous one...
            new = new.add_months(duration._months)
        if duration._years:
            new._year += duration._years
            if new.get_is_calendar_date():
                month_index = (
                    (new._month_of_year - 1) % CALENDAR.MONTHS_IN_YEAR)
                if get_is_leap_year(new._year):
                    max_day_in_new_month = (
                        CALENDAR.DAYS_IN_MONTHS_LEAP[month_index])
                else:
                    max_day_in_new_month = (
                        CALENDAR.DAYS_IN_MONTHS[month_index])
                if new._day_of_month > max_day_in_new_month:
                    # For example, when Feb 29 - 1 year = Feb 28.
                    new._day_of_month = max_day_in_new_month
            elif new.get_is_ordinal_date():
                max_days_in_year = get_days_in_year(new._year)
                if max_days_in_year < new._day_of_year:
                    new._day_of_year = max_days_in_year
            elif new.get_is_week_date():
                max_weeks_in_year = get_weeks_in_year(new._year)
                if max_weeks_in_year < new._week_of_year:
                    new._week_of_year = max_weeks_in_year
        return new

    def _copy(self) -> "TimePoint":
        """Returns an unlinked copy of this instance."""
        new_timepoint = TimePoint(is_empty_instance=True)
        for attr in self.__slots__:
            setattr(new_timepoint, attr, getattr(self, attr))
        new_timepoint._time_zone = self._time_zone._copy()
        return new_timepoint

    def get_props(self) -> list:
        """Return the data properties of this TimePoint as a list of tuples."""
        props = []
        for attr in self.__slots__:
            value = getattr(self, attr, None)
            if callable(getattr(value, "_copy", None)):
                value = value._copy()
            props.append((attr[1:], value))
            # Have sliced attr string to remove leading underscore
        return props

    def __hash__(self) -> int:
        if self._truncated:
            # TODO: Convert truncated TimePoints to UTC when not buggy
            return hash(
                tuple(getattr(self, attr) for attr in self.__slots__))
        point = self.to_utc()
        return hash((*point.get_calendar_date(),
                     *point.get_hour_minute_second()))

    def _cmp(self, other: "TimePoint", op: str) -> bool:
        """Compare self with other, using the chosen operator.

        Args:
            op: The comparison operator/method, one of ["eq", "lt", "le",
                "gt", "ge"].
        """
        if not isinstance(other, TimePoint):
            return NotImplemented
        if self._truncated != other._truncated:
            raise ValueError(
                "Cannot compare truncated to non-truncated "
                "TimePoint: {0}, {1}".format(self, other))
        if self.get_props() == other.get_props():
            return True if op in ["eq", "le", "ge"] else False
        if self._truncated:
            # TODO: Convert truncated TimePoints to UTC when not buggy
            for attribute in self.__slots__:
                self_attr = getattr(self, attribute)
                other_attr = getattr(other, attribute)
                if self_attr != other_attr:
                    return _operator_map[op](self_attr, other_attr)
            return True
        other = other.to_time_zone(self._time_zone)
        if self.get_is_calendar_date():
            my_date = self.get_calendar_date()
            other_date = other.get_calendar_date()
        else:
            my_date = self.get_ordinal_date()
            other_date = other.get_ordinal_date()
        my_datetime = [*my_date, self.get_second_of_day()]
        other_datetime = [*other_date, other.get_second_of_day()]
        return _operator_map[op](my_datetime, other_datetime)

    def __eq__(self, other: "TimePoint") -> bool:
        return self._cmp(other, "eq")

    def __lt__(self, other: "TimePoint") -> bool:
        return self._cmp(other, "lt")

    def __le__(self, other: "TimePoint") -> bool:
        return self._cmp(other, "le")

    def __gt__(self, other: "TimePoint") -> bool:
        return self._cmp(other, "gt")

    def __ge__(self, other: "TimePoint") -> bool:
        return self._cmp(other, "ge")

    def __sub__(self, other):
        if isinstance(other, TimePoint):
            if other > self:
                return -1 * (other - self)
            other = other.to_time_zone(self._time_zone)
            my_year, my_day_of_year = self.get_ordinal_date()
            other_year, other_day_of_year = other.get_ordinal_date()
            diff_day = my_day_of_year - other_day_of_year
            if my_year > other_year:
                diff_day += get_days_in_year_range(other_year, my_year - 1)
            else:
                diff_day -= get_days_in_year_range(my_year, other_year - 1)
            my_hour, my_minute, my_second = self.get_hour_minute_second()
            other_hour, other_minute, other_second = (
                other.get_hour_minute_second())
            diff_hour = my_hour - other_hour
            diff_minute = my_minute - other_minute
            diff_second = my_second - other_second
            if diff_second < 0:
                diff_minute -= 1
                diff_second += CALENDAR.SECONDS_IN_MINUTE
            if diff_minute < 0:
                diff_hour -= 1
                diff_minute += CALENDAR.MINUTES_IN_HOUR
            if diff_hour < 0:
                diff_day -= 1
                diff_hour += CALENDAR.HOURS_IN_DAY
            return Duration(
                days=diff_day, hours=diff_hour, minutes=diff_minute,
                seconds=diff_second)
        if not isinstance(other, Duration):
            raise TypeError(
                "Invalid subtraction type " +
                "'%s' - should be Duration." %
                type(other).__name__
            )
        duration = other
        return self.__add__(duration * -1)

    def add_months(self, num_months):
        """Return a copy of this TimePoint with an amount of months added to
        it."""
        if num_months == 0:
            return self
        new = self._copy()
        was_ordinal_date = False
        was_week_date = False
        if not new.get_is_calendar_date():
            if new.get_is_ordinal_date():
                was_ordinal_date = True
            if new.get_is_week_date():
                was_week_date = True
            new = new.to_calendar_date()
        for _ in range(abs(num_months)):
            if num_months > 0:
                new._month_of_year += 1
                if new._month_of_year > CALENDAR.MONTHS_IN_YEAR:
                    new._month_of_year -= CALENDAR.MONTHS_IN_YEAR
                    new._year += 1
            if num_months < 0:
                new._month_of_year -= 1
                if new._month_of_year < 1:
                    new._month_of_year += CALENDAR.MONTHS_IN_YEAR
                    new._year -= 1
            month_index = (new._month_of_year - 1) % CALENDAR.MONTHS_IN_YEAR
            if get_is_leap_year(new._year):
                max_day_in_new_month = (
                    CALENDAR.DAYS_IN_MONTHS_LEAP[month_index])
            else:
                max_day_in_new_month = (
                    CALENDAR.DAYS_IN_MONTHS[month_index])
            if new._day_of_month > max_day_in_new_month:
                # For example, when 31 March + 1 month = 30 April.
                new._day_of_month = max_day_in_new_month
        new._tick_over()
        if was_ordinal_date:
            new = new.to_ordinal_date()
        if was_week_date:
            new = new.to_week_date()
        return new

    def _tick_over(self, check_changes=False):
        """Correct all the units going from smallest to largest.

        Args:
            check_changes (bool, optional): If True tick_over will return a
                dict of any changed fields.

        Returns:
            dict: Dictionary of changed fields with before and after values
                if check_changes is True else None.
        """
        if check_changes:
            before = {key: getattr(self, key) for key in self.__slots__}
        if (self._hour_of_day is not None and
                self._minute_of_hour is not None):
            hours_remainder = self._hour_of_day - int(self._hour_of_day)
            self._hour_of_day -= hours_remainder
            self._minute_of_hour += (
                hours_remainder * CALENDAR.MINUTES_IN_HOUR)
        if (self._minute_of_hour is not None and
                self._second_of_minute is not None):
            minutes_remainder = (
                self._minute_of_hour - int(self._minute_of_hour))
            self._minute_of_hour -= minutes_remainder
            self._second_of_minute += (
                minutes_remainder * CALENDAR.SECONDS_IN_MINUTE)
        if self._second_of_minute is not None:
            num_minutes, seconds = divmod(self._second_of_minute,
                                          CALENDAR.SECONDS_IN_MINUTE)
            self._minute_of_hour += num_minutes
            self._second_of_minute = seconds
        if self._minute_of_hour is not None:
            num_hours, minutes = divmod(self._minute_of_hour,
                                        CALENDAR.MINUTES_IN_HOUR)
            self._hour_of_day += num_hours
            self._minute_of_hour = minutes
        if self._hour_of_day is not None:
            num_days, hours = divmod(self._hour_of_day, CALENDAR.HOURS_IN_DAY)
            num_days = int(num_days)
            if self._day_of_week is not None:
                self._day_of_week += num_days
            elif self._day_of_month is not None:
                self._day_of_month += num_days
            elif self._day_of_year is not None:
                self._day_of_year += num_days
            self._hour_of_day = hours
        if self._day_of_week is not None:
            num_weeks, days = divmod(
                self._day_of_week - 1, CALENDAR.DAYS_IN_WEEK)
            self._week_of_year += num_weeks
            self._day_of_week = days + 1
        if self._day_of_month is not None:
            self._tick_over_day_of_month()
        if self._day_of_year is not None:
            while self._day_of_year < 1:
                days_in_last_year = get_days_in_year(self._year - 1)
                self._day_of_year += days_in_last_year
                self._year -= 1
            while self._day_of_year > get_days_in_year(self._year):
                days_in_next_year = get_days_in_year(self._year + 1)
                self._day_of_year -= days_in_next_year
                self._year += 1
        if self._week_of_year is not None:
            while self._week_of_year < 1:
                weeks_in_last_year = get_weeks_in_year(self._year - 1)
                self._week_of_year += weeks_in_last_year
                self._year -= 1
            while self._week_of_year > get_weeks_in_year(self._year):
                weeks_in_this_year = get_weeks_in_year(self._year)
                self._week_of_year -= weeks_in_this_year
                self._year += 1
        if self._month_of_year is not None:
            while self._month_of_year < 1:
                self._month_of_year += CALENDAR.MONTHS_IN_YEAR
                self._year -= 1
            while self._month_of_year > CALENDAR.MONTHS_IN_YEAR:
                self._month_of_year -= CALENDAR.MONTHS_IN_YEAR
                self._year += 1
        if check_changes:
            return {
                key: (value, getattr(self, key))
                for key, value in before.items()
                if getattr(self, key) != value
            }

    def _tick_over_day_of_month(self):
        if self._day_of_month < 1:
            num_days = 2
            for month, day in iter_months_days(
                    self._year,
                    month_of_year=self._month_of_year,
                    day_of_month=1, in_reverse=True):
                num_days -= 1
                if num_days == self._day_of_month:
                    self._month_of_year = month
                    self._day_of_month = day
                    break
            else:  # no break
                start_year = self._year
                month = None
                day = None
                while num_days != self._day_of_month:
                    start_year -= 1
                    for month, day in iter_months_days(
                            start_year, in_reverse=True):
                        num_days -= 1
                        if num_days == self._day_of_month:
                            break
                self._year = start_year
                self._month_of_year = month
                self._day_of_month = day
        else:
            month_index = (self._month_of_year - 1) % CALENDAR.MONTHS_IN_YEAR
            if get_is_leap_year(self._year):
                max_day_in_month = CALENDAR.DAYS_IN_MONTHS_LEAP[month_index]
            else:
                max_day_in_month = CALENDAR.DAYS_IN_MONTHS[month_index]
            if self._day_of_month > max_day_in_month:
                num_days = 0
                for month, day in iter_months_days(
                        self._year,
                        month_of_year=self._month_of_year,
                        day_of_month=1):
                    num_days += 1
                    if num_days == self._day_of_month:
                        self._month_of_year = month
                        self._day_of_month = day
                        break
                else:
                    start_year = self._year
                    while num_days != self._day_of_month:
                        start_year += 1
                        for month, day in iter_months_days(start_year):
                            num_days += 1
                            if num_days == self._day_of_month:
                                self._year = start_year
                                self._month_of_year = month
                                self._day_of_month = day
                                return

    def _check_bounds(self):
        """Check all values are within correct bounds."""
        _bounds_checker(self._month_of_year, "month_of_year",
                        min_val=1, max_val=CALENDAR.MONTHS_IN_YEAR)
        if self._month_of_year is not None:
            if self._year is not None:
                max_days_in_month = get_days_in_month(self._month_of_year,
                                                      self._year)
            else:
                max_days_in_month = get_days_in_month(self._month_of_year,
                                                      year="leap")
        else:
            max_days_in_month = CALENDAR.MAX_DAYS_IN_MONTH
        _bounds_checker(self._day_of_month, "day_of_month",
                        min_val=1, max_val=max_days_in_month)
        if self._year is not None:
            _bounds_checker(self._week_of_year, "week_of_year",
                            min_val=1, max_val=get_weeks_in_year(self._year))
            _bounds_checker(self._day_of_year, "day_of_year",
                            min_val=1, max_val=get_days_in_year(self._year))
        else:
            _bounds_checker(self._week_of_year, "week_of_year",
                            min_val=1, max_val=CALENDAR.MAX_WEEKS_IN_YEAR)
            _bounds_checker(self._day_of_year, "day_of_year",
                            min_val=1, max_val=CALENDAR.DAYS_IN_YEAR_LEAP)
        _bounds_checker(self._day_of_week, "day_of_week",
                        min_val=1, max_val=CALENDAR.DAYS_IN_WEEK)

        _bounds_checker(self._hour_of_day, "hour_of_day",
                        min_val=0, max_val=CALENDAR.HOURS_IN_DAY)
        if self._hour_of_day == CALENDAR.HOURS_IN_DAY:
            _bounds_checker(self._minute_of_hour, "minute_of_hour",
                            min_val=0, max_val=0)
            _bounds_checker(self._second_of_minute, "second_of_minute",
                            min_val=0, max_val=0)
        else:
            _bounds_checker(self._minute_of_hour, "minute_of_hour",
                            min_val=0, upper_val=CALENDAR.MINUTES_IN_HOUR)
            _bounds_checker(self._second_of_minute, "second_of_minute",
                            min_val=0, upper_val=CALENDAR.SECONDS_IN_MINUTE)

    def __str__(self, override_custom_dump_format=False,
                strftime_format=None):
        if self._num_expanded_year_digits not in TIMEPOINT_DUMPER_MAP:
            TIMEPOINT_DUMPER_MAP[self._num_expanded_year_digits] = (
                dumpers.TimePointDumper(self._num_expanded_year_digits))
        dumper = TIMEPOINT_DUMPER_MAP[self._num_expanded_year_digits]
        if strftime_format is not None:
            return dumper.strftime(self, strftime_format)
        if self._truncated:
            if self._truncated_dump_format and not override_custom_dump_format:
                return dumper.dump(self, self._truncated_dump_format)
            return dumper.dump(self, self._get_truncated_dump_format())
        if self._dump_format and not override_custom_dump_format:
            return dumper.dump(self, self._dump_format)
        return dumper.dump(self, self._get_dump_format())

    def strftime(self, strftime_format):
        """Implement equivalent of Python 2's datetime.datetime.strftime.

        Dump based on the format given in the strftime_format string.
        """
        return self.__str__(strftime_format=strftime_format)

    def _get_dump_format(self):
        year_digits = 4 + self._num_expanded_year_digits
        year_string = "%0" + str(year_digits) + "d"
        if self._num_expanded_year_digits:
            if self._year < 0:
                year_string = "-" + year_string % abs(self._year)
            else:
                year_string = "+" + year_string % abs(self._year)
        elif self._year is not None and self._year < 0:
            raise OverflowError(
                "Year %s can only be represented in expanded format" %
                self._year
            )
        elif self._year is not None:
            year_string = year_string % self._year

        if self.get_is_calendar_date():
            date_string = year_string + "-MM-DD"
        elif self.get_is_ordinal_date():
            date_string = year_string + "-DDD"
        elif self.get_is_week_date():
            date_string = year_string + "-Www-D"
        else:
            raise RuntimeError("TimePoint has inconsistent state, points "
                               "must conform to calendar, ordinal or week "
                               "dates.")
        time_string = "Thh"
        if self._minute_of_hour is None:
            time_string += ",ii"
        else:
            time_string += ":mm"
            if self._second_of_minute is None:
                time_string += ",nn"
            else:
                seconds_int = int(self._second_of_minute)
                time_string += ":ss"
                if seconds_int != self._second_of_minute:
                    time_string += ",tt"
        if time_string:
            if self._time_zone._hours == 0 and self._time_zone._minutes == 0:
                time_string += "Z"
            else:
                time_string += "+hh:mm"
        return date_string + time_string

    def _get_truncated_dump_format(self):
        year_string = "-"
        if self._truncated_property == "year_of_decade":
            year_string = "-" + "z"
        elif self._truncated_property == "year_of_century":
            if self._day_of_month is None and self._month_of_year is not None:
                year_string = "-YY"
            else:
                year_string = "YY"
        date_string = year_string
        if self._month_of_year is not None:
            date_string = year_string + "-MM"
            if self._day_of_month is not None:
                date_string += "-DD"
        elif self._day_of_month is not None:
            if year_string == "-":
                date_string = year_string + "--DD"
            else:
                date_string = year_string + "-DD"
        if self._day_of_year is not None:
            day_string = "DDD"
            if year_string == "-":
                date_string = year_string + day_string
            else:
                date_string = year_string + "-" + day_string
        if self._week_of_year is not None:
            if year_string == "-":
                date_string = year_string + "Www"
            else:
                date_string = year_string + "-Www"
            if self._day_of_week is not None:
                date_string += "-D"
        elif self._day_of_week is not None:
            if year_string == "-":
                date_string = year_string + "W-D"
            else:
                date_string = year_string + "-W-D"
        time_string = ""
        if (self._hour_of_day is None and
                (self._minute_of_hour is not None or
                 self._second_of_minute is not None)):
            time_string = "T-"
        elif (self._hour_of_day is not None and
              int(self._hour_of_day) != self._hour_of_day):
            time_string = "Thh,ii"
        elif self._hour_of_day is not None:
            time_string = "Thh"
        if self._minute_of_hour is None and self._second_of_minute is not None:
            time_string += "-"
        elif (self._minute_of_hour is not None and
              int(self._minute_of_hour) != self._minute_of_hour):
            if self._hour_of_day is not None:
                time_string += ":"
            time_string += "mm,nn"
        elif self._minute_of_hour is not None:
            if self._hour_of_day is not None:
                time_string += ":"
            time_string += "mm"
        if self._second_of_minute is not None:
            seconds_int = int(self._second_of_minute)
            if self._minute_of_hour is not None:
                time_string += ":"
            time_string += "ss"
            if seconds_int != self._second_of_minute:
                time_string += ",tt"
        if time_string:
            if self._time_zone._hours == 0 and self._time_zone._minutes == 0:
                time_string += "Z"
            else:
                time_string += "+hh:mm"
        if date_string == "YY":
            date_string = "-YY"
            time_string = time_string.replace(":", "")
        if date_string == "-":
            date_string = ""
        return date_string + time_string

    def __repr__(self):
        return "<{0}.{1}: {2}>".format(
            self.__module__, self.__class__.__name__, str(self))


def _format_remainder(float_time_number):
    """Format a floating point remainder of a time unit."""
    string = "," + ("%f" % float_time_number)[2:].rstrip("0")
    if string == ",":
        return ""
    return string


@lru_cache(maxsize=100000)
def get_is_leap_year(year):
    """Return if year is a leap year."""
    year_is_leap = False
    for factor, is_leap_factor in CALENDAR.LEAP_YEAR_FACTOR_TRUTHS:
        if year % factor == 0:
            year_is_leap = is_leap_factor
    return year_is_leap


def get_days_in_year_range(start_year, end_year):
    """Return the number of days within this year range (inclusive)."""
    return _get_days_in_year_range(start_year, end_year, CALENDAR.mode)


@lru_cache(maxsize=100000)
def _get_days_in_year_range(start_year, end_year, _):
    """Return the number of days within this year range (inclusive).

    If end_year > start_year, return the days in start_year plus
    the days in the intervening years before end_year, plus the
    days in end_year.

    If end_year == start_year, return the days in start_year.

    If end_year < start_year, return 0.

    """
    # Get the number of days discounting leap years.
    if start_year == end_year:
        return get_days_in_year(start_year)
    if start_year > end_year:
        return 0
    days = (end_year + 1 - start_year) * CALENDAR.DAYS_IN_YEAR
    diff_days_leap = (CALENDAR.DAYS_IN_YEAR_LEAP - CALENDAR.DAYS_IN_YEAR)
    for factor, is_leap_factor in CALENDAR.LEAP_YEAR_FACTOR_TRUTHS:
        num_corrections = 0
        if start_year % factor == 0:
            num_corrections += 1
        if end_year != start_year and end_year % factor == 0:
            num_corrections += 1
        factor_start_year = start_year + 1
        while (factor_start_year % factor != 0 and
               factor_start_year < end_year):
            factor_start_year += 1
        if factor_start_year < end_year:
            num_corrections += 1
            num_corrections += (
                end_year - (factor_start_year + 1)) // factor
        if is_leap_factor:
            days += num_corrections * diff_days_leap
        else:
            days -= num_corrections * diff_days_leap
    return days


def get_days_in_year(year):
    """Return the number of days in this particular year."""
    return _get_days_in_year(year, CALENDAR.mode)


@lru_cache(maxsize=100000)
def _get_days_in_year(year, _):
    """Return the number of days in this particular year."""
    if get_is_leap_year(year):
        return CALENDAR.DAYS_IN_YEAR_LEAP
    return CALENDAR.DAYS_IN_YEAR


def get_days_in_month(month_of_year, year="leap"):
    """Return the number of days in the month of this particular year.
    Year can also be "leap", or None for non-leap."""
    return _get_days_in_month(month_of_year, year, CALENDAR.mode)


@lru_cache(maxsize=100000)
def _get_days_in_month(month_of_year, year, _):
    """Return the number of days in the month of this particular year.
    Year can also be "leap", or None for non-leap."""
    month_index = month_of_year - 1
    if year is not None and (year == "leap" or get_is_leap_year(year)):
        return CALENDAR.DAYS_IN_MONTHS_LEAP[month_index]
    return CALENDAR.DAYS_IN_MONTHS[month_index]


def get_weeks_in_year(year):
    """Return the number of calendar weeks in this week date year."""
    return _get_weeks_in_year(year, CALENDAR.mode)


@lru_cache(maxsize=100000)
def _get_weeks_in_year(year, _):
    """Return the number of calendar weeks in this week date year."""
    cal_year, cal_ord_days = get_ordinal_date_week_date_start(year)
    cal_year_next, cal_ord_days_next = get_ordinal_date_week_date_start(
        year + 1)
    diff_days = cal_ord_days_next - cal_ord_days
    for intervening_year in range(cal_year, cal_year_next):
        diff_days += get_days_in_year(intervening_year)
    return diff_days // CALENDAR.DAYS_IN_WEEK


def get_calendar_date_from_ordinal_date(year, day_of_year):
    """Translate an ordinal date into a calendar date.

    Returns the calendar year, calendar month, calendar day-of-month.

    Arguments:
    year is an integer that denotes the ordinal date year
    day_of_year is an integer that denotes the ordinal day in the year.

    """
    iter_num_days = 0
    for iter_month, iter_day in iter_months_days(year):
        iter_num_days += 1
        if iter_num_days == day_of_year:
            return year, iter_month, iter_day
    raise ValueError("Bad ordinal date: %s-%03d" % (year, day_of_year))


def get_calendar_date_from_week_date(year, week_of_year, day_of_week):
    """Translate a week date into a calendar date.

    Returns the calendar year, calendar month, calendar day-of-month.

    Arguments:
    year is an integer that denotes the week date year (may differ
    from calendar year)
    week_of_year is an integer that denotes the week number in the year
    day_of_week is an integer that denotes the day of the week (1-7).

    """
    num_days_week_year = (
        (week_of_year - 1) * CALENDAR.DAYS_IN_WEEK + day_of_week - 1)
    start_year, start_month, start_day = (
        get_calendar_date_week_date_start(year))
    if num_days_week_year == 0:
        return start_year, start_month, start_day
    total_iter_days = 0
    # Loop over the months and days left in the start year.
    for iter_month, iter_day in iter_months_days(
            start_year, month_of_year=start_month,
            day_of_month=start_day + 1):
        total_iter_days += 1
        if num_days_week_year == total_iter_days:
            return start_year, iter_month, iter_day
    if start_year < year:
        # We've only looped over the last year - now the current one.
        for iter_month, iter_day in iter_months_days(year):
            total_iter_days += 1
            if num_days_week_year == total_iter_days:
                return year, iter_month, iter_day
    for iter_month, iter_day in iter_months_days(year + 1):
        # Loop over the following year.
        total_iter_days += 1
        if num_days_week_year == total_iter_days:
            return year + 1, iter_month, iter_day
    raise ValueError("Bad week date: %s-W%02d-%s" % (year,
                                                     week_of_year,
                                                     day_of_week))


def get_ordinal_date_from_calendar_date(year, month_of_year, day_of_month):
    """Translate a calendar date into an ordinal date.

    Returns the ordinal year, calendar month, calendar day-of-month.

    Arguments:
    year is an integer that denotes the year
    month_of_year is an integer that denotes the month number in the
    year.
    day_of_month is an integer that denotes the day number in the
    month_of_year.

    """
    iter_num_days = 0
    for iter_month, iter_day in iter_months_days(year):
        iter_num_days += 1
        if iter_month == month_of_year and iter_day == day_of_month:
            return year, iter_num_days
    raise ValueError("Bad calendar date: %s-%02d-%02d" % (year,
                                                          month_of_year,
                                                          day_of_month))


def get_ordinal_date_from_week_date(year, week_of_year, day_of_week):
    """Translate a week date into an ordinal date.

    Returns the ordinal year, ordinal day-of-year.

    Arguments:
    year is an integer that denotes the week date year (which may
    differ from the ordinal or calendar year)
    week_of_year is an integer that denotes the week number in the
    year.
    day_of_week is an integer that denotes the day number in the
    week_of_year.

    """
    cal_year, cal_month, cal_day_of_month = get_calendar_date_from_week_date(
        year, week_of_year, day_of_week)
    return get_ordinal_date_from_calendar_date(
        cal_year, cal_month, cal_day_of_month)


def get_week_date_from_calendar_date(year, month_of_year, day_of_month):
    """Translate a calendar date into an week date.

    Returns the week date year, week-of-year, day-of-week.

    Arguments:
    year is an integer that denotes the calendar year, which may
    differ from the week date year.
    month_of_year is an integer that denotes the month number in the
    above year.
    day_of_month is an integer that denotes the day number in the
    above month_of_year.

    """
    prev_start = get_calendar_date_week_date_start(year - 1)
    this_start = get_calendar_date_week_date_start(year)
    next_start = get_calendar_date_week_date_start(year + 1)

    cal_date = (year, month_of_year, day_of_month)

    if prev_start <= cal_date < this_start:
        # This calendar date is in the previous week date year.
        start_year, start_month, start_day = prev_start
        week_date_start_year = year - 1
    elif this_start <= cal_date < next_start:
        # This calendar date is in the same week date year.
        start_year, start_month, start_day = this_start
        week_date_start_year = year
    else:
        # This calendar date is in the next week date year.
        start_year, start_month, start_day = next_start
        week_date_start_year = year + 1

    total_iter_days = -1
    # A week date year can theoretically span 3 calendar years...
    for iter_month, iter_day in iter_months_days(start_year,
                                                 month_of_year=start_month,
                                                 day_of_month=start_day):
        total_iter_days += 1
        if (start_year == year and
                iter_month == month_of_year and
                iter_day == day_of_month):
            week_of_year = (total_iter_days // CALENDAR.DAYS_IN_WEEK) + 1
            day_of_week = (total_iter_days % CALENDAR.DAYS_IN_WEEK) + 1
            return week_date_start_year, week_of_year, day_of_week

    for iter_start_year in [start_year + 1, start_year + 2]:
        # Look at following year when the calendar date is e.g. very early Jan.
        for iter_month, iter_day in iter_months_days(iter_start_year):
            total_iter_days += 1
            if (iter_start_year == year and
                    iter_month == month_of_year and
                    iter_day == day_of_month):
                week_of_year = (total_iter_days // CALENDAR.DAYS_IN_WEEK) + 1
                day_of_week = (total_iter_days % CALENDAR.DAYS_IN_WEEK) + 1
                return week_date_start_year, week_of_year, day_of_week
    raise ValueError("Bad calendar date: %s-%02d-%02d" % (year,
                                                          month_of_year,
                                                          day_of_month))


def get_week_date_from_ordinal_date(year, day_of_year):
    """Translate an ordinal date into a week date.

    Returns the week date year, week-of-year, day-of-week.

    Arguments:
    year is an integer that denotes the ordinal date year, which
    may differ from the week date year.
    day_of_year is an integer that denotes the ordinal day in the year.

    """
    year, month, day = get_calendar_date_from_ordinal_date(year, day_of_year)
    return get_week_date_from_calendar_date(year, month, day)


def get_calendar_date_week_date_start(year):
    """Return the calendar date of the start of (week date) year."""
    return _get_calendar_date_week_date_start(year, CALENDAR.mode)


@lru_cache(maxsize=100000)
def _get_calendar_date_week_date_start(year, _):
    """Return the calendar date of the start of (week date) year."""
    ref_year, ref_month, ref_day = (
        CALENDAR.WEEK_DAY_START_REFERENCE["calendar"])
    ref_year, ref_ordinal_day = (
        CALENDAR.WEEK_DAY_START_REFERENCE["ordinal"])
    if year == ref_year:
        return ref_year, ref_month, ref_day
    # Calculate the weekday for 1 January in this calendar year.
    days_diff = 0
    if year > ref_year:
        days_diff = 1 - ref_ordinal_day
        days_diff += get_days_in_year_range(ref_year, year - 1)
    elif ref_year > year:
        days_diff = ref_ordinal_day - 2
        days_diff += get_days_in_year_range(year, ref_year - 1)

    weekdays_diff = days_diff % CALENDAR.DAYS_IN_WEEK
    if year > ref_year:
        day_of_week_start_year = weekdays_diff + 1
    else:
        # Jan 1 as day of week.
        day_of_week_start_year = CALENDAR.DAYS_IN_WEEK - weekdays_diff
    if day_of_week_start_year == 1:
        return year, 1, 1
    if day_of_week_start_year > 4:
        # This week belongs to the previous year; get the next Monday.
        day = 1 + (8 - day_of_week_start_year)
        return year, 1, day
    # The week starts in the previous year - get the previous Monday.
    for month, day in iter_months_days(year - 1, in_reverse=True):
        day_of_week_start_year -= 1
        if day_of_week_start_year == 1:
            return year - 1, month, day


def get_days_since_1_ad(year):
    """Return the number of days since Jan 1, 1 A.D. to the year end."""
    return _get_days_since_1_ad(year, CALENDAR.mode)


@lru_cache(maxsize=100000)
def _get_days_since_1_ad(year, _):
    """Return the number of days since Jan 1, 1 A.D. to the year end."""
    if year == 1:
        return get_days_in_year(year)
    elif year < 1:
        return 0
    return get_days_in_year_range(1, year)


def get_ordinal_date_week_date_start(year):
    """Return the ordinal week date start for year (year, day-of-year)."""
    return _get_ordinal_date_week_date_start(year, CALENDAR.mode)


@lru_cache(maxsize=100000)
def _get_ordinal_date_week_date_start(year, _):
    """Return the ordinal week date start for year (year, day-of-year)."""
    cal_year, cal_month, cal_day = get_calendar_date_week_date_start(year)
    total_days = 0
    for iter_month, iter_day in iter_months_days(cal_year):
        total_days += 1
        if iter_month == cal_month and iter_day == cal_day:
            return cal_year, total_days


def get_timepoint_for_now(utc=False):
    """Return a TimePoint at the current date/time.

     Args:
        utc (bool): Whether the returned TimePoint should be in UTC or the
            local time zone.
    """
    import time
    return get_timepoint_from_seconds_since_unix_epoch(time.time(), utc=utc)


def get_timepoint_from_seconds_since_unix_epoch(num_seconds, utc=False):
    """Return a TimePoint at a date/time specified in Unix time.

    Args:
        num_seconds (float): The number of seconds since the Unix epoch.
        utc (bool): Whether the returned TimePoint should be in UTC or the
            local time zone.

    Note that Unix time always counts 1 day = 86400 seconds, so if
    we implement leap seconds we need to make the distinction.
    """
    reference_timepoint = TimePoint(
        **CALENDAR.UNIX_EPOCH_DATE_TIME_REFERENCE_PROPERTIES)
    if not utc:
        reference_timepoint = reference_timepoint.to_local_time_zone()
    return reference_timepoint + Duration(seconds=float(num_seconds))


def get_timepoint_properties_from_seconds_since_unix_epoch(num_seconds):
    """Translate Unix time into a dict of TimePoint constructor properties."""
    properties = dict(
        get_timepoint_from_seconds_since_unix_epoch(num_seconds).get_props())
    time_zone = properties.pop("time_zone")
    properties["time_zone_hour"] = time_zone._hours
    properties["time_zone_minute"] = time_zone._minutes
    return properties


def iter_months_days(year, month_of_year=None, day_of_month=None,
                     in_reverse=False):
    """Iterate over each day in each month of year.

    year is an integer specifying the year to use.
    month_of_year is an optional integer, specifying a start month.
    day_of_month is an optional integer, specifying a start day.
    in_reverse is an optional boolean that reverses the iteration if
    True (default False).

    """
    is_leap_year = get_is_leap_year(year)
    return _iter_months_days(
        is_leap_year, month_of_year, day_of_month, CALENDAR.mode, in_reverse)


@lru_cache(maxsize=100000)
def _iter_months_days(is_leap_year, month_of_year, day_of_month, _,
                      in_reverse=False):
    if day_of_month is not None and month_of_year is None:
        raise ValueError("Need to specify start month as well as day.")
    source = CALENDAR.INDEXED_DAYS_IN_MONTHS
    if is_leap_year:
        source = CALENDAR.INDEXED_DAYS_IN_MONTHS_LEAP
    results = []
    if in_reverse:
        if month_of_year is None:
            for month_num, days in reversed(source):
                day_range = range(days, 0, -1)
                for day in day_range:
                    results.append((month_num, day))
        else:
            for month_num, days in reversed(source):
                if month_num > month_of_year:
                    continue
                elif month_num == month_of_year and day_of_month is not None:
                    day_range = range(day_of_month, 0, -1)
                else:
                    day_range = range(days, 0, -1)
                for day in day_range:
                    results.append((month_num, day))
    else:
        if month_of_year is None:
            for month_num, days in source:
                day_range = range(1, days + 1)
                for day in day_range:
                    results.append((month_num, day))
        else:
            for month_num, days in source[month_of_year - 1:]:
                if month_num == month_of_year and day_of_month is not None:
                    day_range = range(day_of_month, days + 1)
                else:
                    day_range = range(1, days + 1)
                for day in day_range:
                    results.append((month_num, day))
    return results


def _int_caster(number, name="number", allow_none=False):
    if allow_none and number is None:
        return None
    try:
        int_number = int(number)
        float_number = float(number)
    except (TypeError, ValueError) as num_exc:
        raise BadInputError(
            BadInputError.INT_CAST, name, number, num_exc)
    if float(int_number) != float_number:
        raise BadInputError(
            BadInputError.INT_REMAINDER, name, number)
    return int_number


def _type_checker(*objects):
    """Helper function for checking the type of method arguments.

    Args:
        *objects: Tuples of the form (value, name, *allowed_types):

    Raises:
        BadInputError: If a value is not of the correct type.
    """
    for type_info in objects:
        value, name = type_info[:2]
        allowed_types = list(type_info[2:])
        none_is_allowed = False
        if None in allowed_types:
            if value is None:
                continue
            none_is_allowed = True
            allowed_types.remove(None)
            allowed_types.append(type(None))
        if allowed_types and isinstance(value, allowed_types[0]):
            continue
        if int in allowed_types and float not in allowed_types:
            value = _int_caster(value, name=name, allow_none=none_is_allowed)
        if any(isinstance(value, type_) for type_ in allowed_types):
            continue
        values_string = ""
        if allowed_types:
            values_string = " should be: "
            values_string += " or ".join(str(v) for v in allowed_types)
        raise BadInputError(
            BadInputError.TYPE, name, repr(value), values_string)


def _bounds_checker(value, name, min_val, max_val=None, upper_val=None):
    """Helper function for checking the value of a property is within bounds.

    Args:
        value (None, float): The value to check.
        name (str): Name of the property.
        min_val (float): Minimum value, inclusive.
        max_val (float, optional): Maximum value, inclusive.
        upper_val (float, optional): Upper limit of value, not inclusive.

    Raises:
        BadInputError: If the value is out of bounds.
    """
    if (value is not None and
            (value < min_val or
             (max_val is not None and value > max_val) or
             (upper_val is not None and value >= upper_val))):
        raise BadInputError(BadInputError.OUT_OF_BOUNDS, name, value)


PARSE_PROPERTY_TRANSLATORS = {
    "seconds_since_unix_epoch":
        get_timepoint_properties_from_seconds_since_unix_epoch
}
