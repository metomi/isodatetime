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

"""This tests the ISO 8601 parsing and data model functionality."""

import datetime
import pytest
import random

from metomi.isodatetime.data import TimePoint, Duration, get_days_since_1_ad


def daterange(start_date, end_date):
    """https://stackoverflow.com/a/1060330"""
    for n in range(1 + int((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)


test_duration_attributes = [
                ("weeks", 110),
                ("days", 770),
                ("hours", 770 * 24),
                ("minutes", 770 * 24 * 60),
                ("seconds", 770 * 24 * 60 * 60)
            ]


@pytest.mark.slow
@pytest.mark.parametrize('century', range(18, 24))
def test_timepoint(century):
    """Test the time point data model (takes a while).

    For a range of years (e.g. 1800 to 2400) it iterates through each
    year, then creates another range with the days in this year. Finally
    performs a series of tests, failing if any operation results in
    an error."""
    for test_year in range(century * 100, (century + 1) * 100, 1):
        _test_timepoint(test_year)


def _test_timepoint(test_year):
    my_date = datetime.datetime(test_year, 1, 1)
    stop_date = datetime.datetime(test_year + 1, 1, 1)
    for date in daterange(my_date, stop_date):
        ctrl_data = date.isocalendar()
        test_date = TimePoint(
            year=date.year,
            month_of_year=date.month,
            day_of_month=date.day
        )
        test_week_date = test_date.to_week_date()
        test_data = test_week_date.get_week_date()
        assert test_data == ctrl_data
        ctrl_data = (date.year, date.month, date.day)
        test_data = test_week_date.get_calendar_date()
        assert test_data == ctrl_data
        ctrl_data = date.toordinal()
        year, day_of_year = test_date.get_ordinal_date()
        test_data = day_of_year
        test_data += get_days_since_1_ad(year - 1)
        assert test_data == ctrl_data
        for attribute, attr_max in test_duration_attributes:
            kwargs = {attribute: random.randrange(0, attr_max)}
            ctrl_data = date + datetime.timedelta(**kwargs)
            ctrl_data = ctrl_data.year, ctrl_data.month, ctrl_data.day
            test_data = (
                (test_date + Duration(**kwargs)).get_calendar_date())
            assert test_data == ctrl_data
            ctrl_data = date - datetime.timedelta(**kwargs)
            ctrl_data = ctrl_data.year, ctrl_data.month, ctrl_data.day
            # TBD: the subtraction is quite slow. Much slower than other
            # operations. Could be related to the fact it converts the
            # value in kwargs to negative multiplying by -1 (i.e. from
            # __sub__ to __mul__), and also adds it to the date (i.e.
            # __add__).  Profiling the tests, the __sub__ operation used in
            # the next line will appear amongst the top of time consuming
            # operations.
            test_data = (
                (test_date - Duration(**kwargs)).get_calendar_date())
            assert test_data == ctrl_data
        kwargs = {}
        for attribute, attr_max in test_duration_attributes:
            kwargs[attribute] = random.randrange(0, attr_max)
        test_date_minus = test_date - Duration(**kwargs)
        test_data = test_date - test_date_minus
        ctrl_data = Duration(**kwargs)
        assert test_data == ctrl_data
        test_data = test_date_minus + (test_date - test_date_minus)
        ctrl_data = test_date
        assert test_data == ctrl_data
        test_data = (test_date_minus + Duration(**kwargs))
        ctrl_data = test_date
        assert test_data == ctrl_data
        ctrl_data = (
            date +
            datetime.timedelta(minutes=450) +
            datetime.timedelta(hours=5) -
            datetime.timedelta(seconds=500, weeks=5))
        ctrl_data = [
            (ctrl_data.year, ctrl_data.month, ctrl_data.day),
            (ctrl_data.hour, ctrl_data.minute, ctrl_data.second)]
        test_data = (
            test_date + Duration(minutes=450) +
            Duration(hours=5) -
            Duration(weeks=5, seconds=500)
        )
        test_data = [
            test_data.get_calendar_date(),
            test_data.get_hour_minute_second()]
        assert test_data == ctrl_data
