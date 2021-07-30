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

"""This provides utilities for extracting the local time zone."""

import time
from typing import Tuple


class TimeZoneFormatMode(object):
    normal = "normal"
    reduced = "reduced"
    extended = "extended"

    templates = {
        normal: '{sign}{hh:02d}{mm:02d}',
        reduced: '{sign}{hh:02d}',
        extended: '{sign}{hh:02d}:{mm:02d}'
    }


def get_local_time_zone() -> Tuple[int, int]:
    """Return the current local UTC offset in hours and minutes."""
    utc_offset_seconds = -time.timezone
    if time.localtime().tm_isdst == 1 and time.daylight:
        utc_offset_seconds = -time.altzone
    sign = -1 if utc_offset_seconds < 0 else 1
    utc_offset_minutes = (utc_offset_seconds // 60) % (sign * 60)
    utc_offset_hours = sign * ((sign * utc_offset_seconds) // 3600)
    return utc_offset_hours, utc_offset_minutes


def get_local_time_zone_format(
    tz_fmt_mode: str = TimeZoneFormatMode.normal
) -> str:
    """Return a string denoting the current local UTC offset.

    :param tz_fmt_mode:
    :type tz_fmt_mode: TimeZoneFormat:
    """
    utc_offset_hours, utc_offset_minutes = get_local_time_zone()
    if utc_offset_hours == utc_offset_minutes == 0:
        return "Z"
    if tz_fmt_mode == TimeZoneFormatMode.reduced and utc_offset_minutes != 0:
        tz_fmt_mode = TimeZoneFormatMode.normal
    sign = "-" if (utc_offset_hours < 0 or utc_offset_minutes < 0) else "+"
    timezone_template = TimeZoneFormatMode.templates[tz_fmt_mode]
    return timezone_template.format(
        sign=sign, hh=abs(utc_offset_hours), mm=abs(utc_offset_minutes)
    )
