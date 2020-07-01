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


class IsodatetimeError(Exception):
    """Generic exception for Isodatetime errors.

    This exception is raised in-place of "expected" errors where a short
    message to the user is more appropriate than traceback.


    """


class BadInputError(IsodatetimeError, ValueError):

    """An error raised when constructor inputs are invalid."""

    CONFLICT = "Conflicting input: {0} but have {1}"
    INT_CAST = "Invalid input for {0}: {1}: {2}"
    INT_REMAINDER = "Non-integer like number for {0}: {1}"
    MISSING = "Missing input: {0} needs {1}"
    OUT_OF_BOUNDS = "Invalid input (out of bounds): {0}: {1}"
    RECURRENCE = "Invalid recurrence info: {0}"
    TYPE = "Invalid type for {0}: {1}{2}"
    VALUES = "Invalid input for {0}: {1}: allowed: {2}"

    def __str__(self):
        format_string = self.args[0]
        format_args = self.args[1:]
        return format_string.format(*format_args)


class OffsetValueError(IsodatetimeError, ValueError):

    """Bad offset value."""

    def __str__(self):
        return "%s: bad offset value" % self.args[0]


class TimePointDumperBoundsError(IsodatetimeError, ValueError):

    """An error raised when a TimePoint can't be dumped within bounds."""

    MESSAGE = "Cannot dump TimePoint {0}: {1} not in bounds {2} to {3}."

    def __str__(self):
        return self.MESSAGE.format(*self.args)


class StrftimeSyntaxError(IsodatetimeError, ValueError):

    """An error denoting invalid or unsupported strftime/strptime syntax."""

    BAD_STRFTIME_INPUT = "Invalid strftime/strptime representation: {0}"

    def __str__(self):
        return self.BAD_STRFTIME_INPUT.format(*self.args)


class ISO8601SyntaxError(IsodatetimeError, ValueError):

    """An error denoting invalid input syntax."""

    BAD_TIME_INPUT = "Invalid ISO 8601 {0} representation: {1}"

    def __str__(self):
        return self.BAD_TIME_INPUT.format(*self.args)


class StrptimeConversionError(IsodatetimeError, ValueError):

    """An error denoting bad conversion from a strftime/strptime format."""

    BAD_CONVERSION = "Bad conversion for strftime/strptime input '{0}': '{1}'"

    def __str__(self):
        return self.BAD_CONVERSION.format(*self.args)
