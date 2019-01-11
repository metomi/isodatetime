# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
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
# ----------------------------------------------------------------------------

"""This tests the ISO 8601 parsing and data model functionality."""

import datetime
import random
import unittest

from isodatetime.data import TimePoint, Duration, get_days_since_1_ad


class TestTimePointCompat(unittest.TestCase):
    """Test time point compatibility with "datetime"."""

    def test_timepoint(self):
        """Test the time point data model (takes a while)."""
        for test_year in range(1801, 2403):
            my_date = datetime.datetime(test_year, 1, 1)
            stop_date = datetime.datetime(test_year + 1, 1, 1)
            test_duration_attributes = [
                ("weeks", 110),
                ("days", 770),
                ("hours", 770 * 24),
                ("minutes", 770 * 24 * 60),
                ("seconds", 770 * 24 * 60 * 60)
            ]
            while my_date <= stop_date:
                ctrl_data = my_date.isocalendar()
                test_date = TimePoint(
                    year=my_date.year,
                    month_of_year=my_date.month,
                    day_of_month=my_date.day
                )
                test_week_date = test_date.to_week_date()
                test_data = test_week_date.get_week_date()
                self.assertEqual(test_data, ctrl_data)
                ctrl_data = (my_date.year, my_date.month, my_date.day)
                test_data = test_week_date.get_calendar_date()
                self.assertEqual(test_data, ctrl_data)
                ctrl_data = my_date.toordinal()
                year, day_of_year = test_date.get_ordinal_date()
                test_data = day_of_year
                test_data += get_days_since_1_ad(year - 1)
                self.assertEqual(test_data, ctrl_data)
                for attribute, attr_max in test_duration_attributes:
                    kwargs = {attribute: random.randrange(0, attr_max)}
                    ctrl_data = my_date + datetime.timedelta(**kwargs)
                    ctrl_data = ctrl_data.year, ctrl_data.month, ctrl_data.day
                    test_data = (
                        (test_date + Duration(**kwargs)).get_calendar_date())
                    self.assertEqual(test_data, ctrl_data)
                    ctrl_data = my_date - datetime.timedelta(**kwargs)
                    ctrl_data = ctrl_data.year, ctrl_data.month, ctrl_data.day
                    test_data = (
                        (test_date - Duration(**kwargs)).get_calendar_date())
                    self.assertEqual(test_data, ctrl_data)
                kwargs = {}
                for attribute, attr_max in test_duration_attributes:
                    kwargs[attribute] = random.randrange(0, attr_max)
                test_date_minus = test_date - Duration(**kwargs)
                test_data = test_date - test_date_minus
                ctrl_data = Duration(**kwargs)
                self.assertEqual(test_data, ctrl_data)
                test_data = test_date_minus + (test_date - test_date_minus)
                ctrl_data = test_date
                self.assertEqual(test_data, ctrl_data)
                test_data = (test_date_minus + Duration(**kwargs))
                ctrl_data = test_date
                self.assertEqual(test_data, ctrl_data)
                ctrl_data = (
                    my_date +
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
                self.assertEqual(test_data, ctrl_data)
                timedelta = datetime.timedelta(days=1)
                my_date += timedelta


if __name__ == '__main__':
    unittest.main()
