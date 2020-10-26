# -*- coding: utf-8 -*-
# pragma pylint: disable=pointless-statement
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
"""This tests the ISO 8601 data model functionality."""

import pytest
import unittest

from metomi.isodatetime import data
from metomi.isodatetime.exceptions import BadInputError


def get_timeduration_tests():
    """Yield tests for the duration class."""
    tests = {
        "get_days_and_seconds": [
            ([], {"hours": 25}, (1, 3600)),
            ([], {"seconds": 59}, (0, 59)),
            ([], {"minutes": 10}, (0, 600)),
            ([], {"days": 5, "minutes": 2}, (5, 120)),
            ([], {"hours": 2, "minutes": 5, "seconds": 11.5}, (0, 7511.5)),
            ([], {"hours": 23, "minutes": 1446}, (1, 83160))
        ],
        "get_seconds": [
            ([], {"hours": 25}, 90000),
            ([], {"seconds": 59}, 59),
            ([], {"minutes": 10}, 600),
            ([], {"days": 5, "minutes": 2}, 432120),
            ([], {"hours": 2, "minutes": 5, "seconds": 11.5}, 7511.5),
            ([], {"hours": 23, "minutes": 1446}, 169560)
        ]
    }
    for method, method_tests in tests.items():
        for method_args, test_props, ctrl_results in method_tests:
            yield test_props, method, method_args, ctrl_results


def get_duration_subtract_tests():
    """Yield tests for subtracting a duration from a timepoint."""
    return [
        {
            "start": {
                "year": 2010, "day_of_year": 65,
                # "month_of_year": 3, "day_of_month": 6,
                "hour_of_day": 12, "minute_of_hour": 0, "second_of_minute": 0,
                "time_zone_hour": 0, "time_zone_minute": 0
            },
            "duration": {
                "years": 6
            },
            "result": {
                "year": 2004,  # "day_of_year": 65,
                "month_of_year": 3, "day_of_month": 5,
                "hour_of_day": 12, "minute_of_hour": 0, "second_of_minute": 0,
                "time_zone_hour": 0, "time_zone_minute": 0
            }
        },
        {
            "start": {
                "year": 2010, "week_of_year": 10, "day_of_week": 3,
                # "month_of_year": 3, "day_of_month": 10,
                "hour_of_day": 12, "minute_of_hour": 0, "second_of_minute": 0,
                "time_zone_hour": 0, "time_zone_minute": 0
            },
            "duration": {
                "years": 6
            },
            "result": {
                "year": 2004,  # "week_of_year": 10, "day_of_week": 3,
                "month_of_year": 3, "day_of_month": 3,
                "hour_of_day": 12, "minute_of_hour": 0, "second_of_minute": 0,
                "time_zone_hour": 0, "time_zone_minute": 0
            }
        },
    ]


def get_duration_comparison_tests():
    """Yield tests for executing comparison operators on Durations.

    All True "==" tests will be carried out for "<=" & ">= too. Likewise
    all True "<" & "> tests will be carried out for "<=" & ">=" respectively.

    Tuple format --> test:
    (args1, args2, bool1 [, bool2]) -->
        Duration(**args1) <operator> Duration(**args2) is bool1
    & the reverse:
        Duration(**args2) <operator> Duration(**args1) is bool2 if
            bool2 supplied else bool1
    """
    nominal_units = ["years", "months"]
    # TODO: test in different calendars
    return {
        "==": [
            # Durations of same type:
            *[({prop: 1}, {prop: 1}, True) for prop in nominal_units],
            *[(dur, dur, True) for dur in [
                {"years": 1, "months": 1, "days": 1}]],
            *[({prop: 1}, {prop: 2}, False) for prop in nominal_units],
            # Nominal durations of different type unequal:
            ({"years": 1}, {"months": 12}, False),
            *[({"years": 1}, {"days": i}, False) for i in [365, 366]],
            *[({"months": 1}, {"days": i}, False) for i in [28, 29, 30, 31]],
            ({"months": 1, "days": 7}, {"weeks": 1}, False),
            # Non-nominal/exact durations of different types equal:
            ({"weeks": 1}, {"days": 7}, True),
            ({"weeks": 1}, {"hours": 7 * 24}, True),
            ({"days": 1}, {"hours": 24}, True),
            ({"days": 1}, {"seconds": 24 * 60 * 60}, True),
            ({"hours": 1}, {"minutes": 60}, True),
            ({"hours": 1}, {"minutes": 30, "seconds": 30 * 60}, True),
            ({"hours": 1.5}, {"minutes": 90}, True)
        ],
        "<": [
            # Durations of same type:
            *[({prop: 1}, {prop: 1}, False) for prop in nominal_units],
            *[(dur, dur, False) for dur in [
                {"years": 1, "months": 1, "days": 1}]],
            *[({prop: 1}, {prop: 2}, True, False) for prop in nominal_units],
            # Durations of different type:
            ({"years": 1}, {"months": 12}, False, True),
            ({"years": 1}, {"months": 12, "days": 10}, True, False),
            ({"years": 1}, {"days": 364}, False, True),
            ({"years": 1}, {"days": 365}, False),
            ({"years": 1}, {"days": 366}, True, False),
            ({"months": 1}, {"days": 29}, False, True),
            ({"months": 1}, {"days": 30}, False),
            ({"months": 1}, {"days": 31}, True, False),
            ({"weeks": 1}, {"days": 6}, False, True),
            ({"weeks": 1}, {"days": 7}, False),
            ({"weeks": 1}, {"days": 8}, True, False),
            ({"days": 1}, {"seconds": 24 * 60 * 60 - 1}, False, True),
            ({"days": 1}, {"seconds": 24 * 60 * 60}, False),
            ({"days": 1}, {"seconds": 24 * 60 * 60 + 1}, True, False),
        ],
        "<=": [
            ({"years": 1}, {"days": 365}, True),
            ({"months": 1}, {"days": 30}, True),
        ],
        ">": [
            # Durations of same type:
            *[({prop: 1}, {prop: 1}, False) for prop in nominal_units],
            *[({prop: 2}, {prop: 1}, True, False) for prop in nominal_units],
            # Ddurations of different type:
            ({"years": 1}, {"months": 12}, True, False),
            ({"years": 1}, {"days": 364}, True, False),
            ({"years": 1}, {"days": 365}, False),
            ({"years": 1}, {"days": 366}, False, True),
            ({"months": 1}, {"days": 29}, True, False),
            ({"months": 1}, {"days": 30}, False),
            ({"months": 1}, {"days": 31}, False, True),
            ({"weeks": 1}, {"days": 6}, True, False),
            ({"weeks": 1}, {"days": 7}, False),
            ({"weeks": 1}, {"days": 8}, False, True),
            ({"days": 1}, {"seconds": 24 * 60 * 60 - 1}, True, False),
            ({"days": 1}, {"seconds": 24 * 60 * 60}, False),
            ({"days": 1}, {"seconds": 24 * 60 * 60 + 1}, False, True),
        ],
        ">=": [
            ({"years": 1}, {"days": 365}, True),
            ({"months": 1}, {"days": 30}, True),
        ]
    }


def get_timepoint_subtract_tests():
    """Yield tests for subtracting one timepoint from another."""
    return [
        (
            {"year": 44, "month_of_year": 1, "day_of_month": 4,
             "hour_of_day": 5, "minute_of_hour": 1, "second_of_minute": 2,
             "time_zone_hour": 0, "time_zone_minute": 0},
            {"year": 41, "month_of_year": 12, "day_of_month": 2,
             "hour_of_day": 4, "minute_of_hour": 23, "second_of_minute": 1,
             "time_zone_hour": 3, "time_zone_minute": 20},
            "P763DT3H58M1S"
        ),
        (
            {"year": 41, "month_of_year": 12, "day_of_month": 2,
             "hour_of_day": 4, "minute_of_hour": 23, "second_of_minute": 1,
             "time_zone_hour": 3, "time_zone_minute": 20},
            {"year": 44, "month_of_year": 1, "day_of_month": 4,
             "hour_of_day": 5, "minute_of_hour": 1, "second_of_minute": 2,
             "time_zone_hour": 0, "time_zone_minute": 0},
            "-P763DT3H58M1S"
        ),
        (
            {"year": 1991, "month_of_year": 6, "day_of_month": 3,
             "hour_of_day": 0, "time_zone_hour": 0, "time_zone_minute": 0},
            {"year": 1991, "month_of_year": 5, "day_of_month": 4,
             "hour_of_day": 5, "time_zone_hour": 0, "time_zone_minute": 0},
            "P29DT19H"
        ),
        (
            {"year": 1969, "month_of_year": 7, "day_of_month": 20,
             "hour_of_day": 20, "time_zone_hour": 0, "time_zone_minute": 0},
            {"year": 1969, "month_of_year": 7, "day_of_month": 20,
             "hour_of_day": 19, "time_zone_hour": 0, "time_zone_minute": 0},
            "PT1H"
        ),

        (
            {"year": 1969, "month_of_year": 7, "day_of_month": 20,
             "hour_of_day": 19, "time_zone_hour": 0, "time_zone_minute": 0},
            {"year": 1969, "month_of_year": 7, "day_of_month": 20,
             "hour_of_day": 20, "time_zone_hour": 0, "time_zone_minute": 0},
            "-PT1H"
        ),
        (
            {"year": 1991, "month_of_year": 5, "day_of_month": 4,
             "hour_of_day": 5, "time_zone_hour": 0, "time_zone_minute": 0},
            {"year": 1991, "month_of_year": 6, "day_of_month": 3,
             "hour_of_day": 0, "time_zone_hour": 0, "time_zone_minute": 0},
            "-P29DT19H"
        ),
        (
            {"year": 2014, "month_of_year": 1, "day_of_month": 1,
             "hour_of_day": 0, "time_zone_hour": 0, "time_zone_minute": 0},
            {"year": 2013, "month_of_year": 12, "day_of_month": 31,
             "hour_of_day": 23, "time_zone_hour": 0, "time_zone_minute": 0},
            "PT1H"
        ),
        (
            {"year": 2013, "month_of_year": 12, "day_of_month": 31,
             "hour_of_day": 23, "time_zone_hour": 0, "time_zone_minute": 0},
            {"year": 2014, "month_of_year": 1, "day_of_month": 1,
             "hour_of_day": 0, "time_zone_hour": 0, "time_zone_minute": 0},
            "-PT1H"
        ),
        (
            {"year": 2014, "month_of_year": 1, "day_of_month": 1,
             "hour_of_day": 0, "time_zone_hour": 0, "time_zone_minute": 0},
            {"year": 2013, "month_of_year": 12, "day_of_month": 1,
             "hour_of_day": 0, "time_zone_hour": 0, "time_zone_minute": 0},
            "P31D"
        ),
        (
            {"year": 2013, "month_of_year": 12, "day_of_month": 1,
             "hour_of_day": 0, "time_zone_hour": 0, "time_zone_minute": 0},
            {"year": 2014, "month_of_year": 1, "day_of_month": 1,
             "hour_of_day": 0, "time_zone_hour": 0, "time_zone_minute": 0},
            "-P31D"
        ),
        (
            {"year": 44, "month_of_year": 1, "day_of_month": 4,
             "hour_of_day": 5, "minute_of_hour": 1, "second_of_minute": 2,
             "time_zone_hour": 0, "time_zone_minute": 0},
            {"year": 41, "month_of_year": 12, "day_of_month": 2,
             "hour_of_day": 13, "minute_of_hour": 23, "second_of_minute": 1,
             "time_zone_hour": 3, "time_zone_minute": 20},
            "P762DT18H58M1S"
        ),
        (
            {"year": 41, "month_of_year": 12, "day_of_month": 2,
             "hour_of_day": 13, "minute_of_hour": 23, "second_of_minute": 1,
             "time_zone_hour": 3, "time_zone_minute": 20},
            {"year": 44, "month_of_year": 1, "day_of_month": 4,
             "hour_of_day": 5, "minute_of_hour": 1, "second_of_minute": 2,
             "time_zone_hour": 0, "time_zone_minute": 0},
            "-P762DT18H58M1S"
        ),
    ]


def get_timepoint_comparison_tests():
    """Yield tests for executing comparison operators on TimePoints.

    All True "==" tests will be carried out for "<=" & ">= too. Likewise
    all True "<" & "> tests will be carried out for "<=" & ">=" respectively.

    Tuple format --> test:
    (args1, args2, bool1 [, bool2]) -->
        TimePoint(**args1) <operator> TimePoint(**args2) is bool1
    & the reverse:
        TimePoint(**args2) <operator> TimePoint(**args1) is bool2 if
            bool2 supplied else bool1
    """
    base_YMD = {"year": 2020, "month_of_year": 3, "day_of_month": 14}
    trunc = {"truncated": True}
    return {
        "==": [
            (base_YMD, base_YMD, True),
            ({"year": 2020, "month_of_year": 2, "day_of_month": 5},
             {"year": 2020, "day_of_year": 36},
             True),
            ({"year": 2019, "month_of_year": 12, "day_of_month": 30},
             {"year": 2020, "week_of_year": 1, "day_of_week": 1},
             True),
            ({"year": 2019, "day_of_year": 364},
             {"year": 2020, "week_of_year": 1, "day_of_week": 1},
             True),
            ({**base_YMD, "hour_of_day": 9, "time_zone_hour": 0},
             {**base_YMD, "hour_of_day": 11, "minute_of_hour": 30,
              "time_zone_hour": 2, "time_zone_minute": 30},
             True),
            ({"month_of_year": 3, "day_of_month": 14, **trunc},
             {"month_of_year": 3, "day_of_month": 14, **trunc},
             True),
            # Truncated datetimes of different modes can't be equal:
            ({"month_of_year": 2, "day_of_month": 5, **trunc},
             {"day_of_year": 36, **trunc},
             False),
            ({"month_of_year": 12, "day_of_month": 30, **trunc},
             {"week_of_year": 1, "day_of_week": 1, **trunc},
             False),
            ({"day_of_year": 364, **trunc},
             {"week_of_year": 1, "day_of_week": 1, **trunc},
             False)
            # TODO: test equal truncated datetimes with different timezones
            # when not buggy
        ],
        "<": [
            (base_YMD, base_YMD, False),
            ({"year": 2019}, {"year": 2020}, True, False),
            ({"year": -1}, {"year": 1}, True, False),
            ({"year": 2020, "month_of_year": 2},
             {"year": 2020, "month_of_year": 3},
             True, False),
            ({"year": 2020, "month_of_year": 2, "day_of_month": 5},
             {"year": 2020, "month_of_year": 2, "day_of_month": 6},
             True, False),
            ({**base_YMD, "hour_of_day": 9}, {**base_YMD, "hour_of_day": 10},
             True, False),
            ({**base_YMD, "hour_of_day": 9, "time_zone_hour": 0},
             {**base_YMD, "hour_of_day": 7, "time_zone_hour": -3},
             True, False),
            ({"day_of_month": 3, **trunc}, {"day_of_month": 4, **trunc},
             True, False),
            ({"month_of_year": 1, "day_of_month": 3, **trunc},
             {"month_of_year": 1, "day_of_month": 4, **trunc},
             True, False)
        ],
        ">": [
            (base_YMD, base_YMD, False),
            ({"year": 2019}, {"year": 2020}, False, True),
            ({"year": -1}, {"year": 1}, False, True),
            ({"year": 2020, "month_of_year": 2},
             {"year": 2020, "month_of_year": 3},
             False, True),
            ({"year": 2020, "month_of_year": 2, "day_of_month": 5},
             {"year": 2020, "month_of_year": 2, "day_of_month": 6},
             False, True),
            ({**base_YMD, "hour_of_day": 9}, {**base_YMD, "hour_of_day": 10},
             False, True),
            ({**base_YMD, "hour_of_day": 9, "time_zone_hour": 0},
             {**base_YMD, "hour_of_day": 7, "time_zone_hour": -3},
             False, True),
            ({"day_of_month": 3, **trunc}, {"day_of_month": 4, **trunc},
             False, True),
            ({"month_of_year": 1, "day_of_month": 3, **trunc},
             {"month_of_year": 1, "day_of_month": 4, **trunc},
             False, True)
        ]
    }


def get_timepoint_bounds_tests():
    """Yield tests for checking out of bounds TimePoints."""
    return {
        "in_bounds": [
            {"year": 2020, "month_of_year": 2, "day_of_month": 29},
            {"truncated": True, "month_of_year": 2, "day_of_month": 29},
            {"year": 2020, "week_of_year": 53},
            {"truncated": True, "week_of_year": 53},
            {"year": 2020, "day_of_year": 366},
            {"truncated": True, "day_of_year": 366},

            {"year": 2019, "hour_of_day": 24},
            {"year": 2019, "time_zone_hour": 99},
            {"year": 2019, "time_zone_hour": 0, "time_zone_minute": -1},
            {"year": 2019, "time_zone_hour": 0, "time_zone_minute": 1},
            {"year": 2019, "time_zone_hour": -1, "time_zone_minute": -1},
        ],
        "out_of_bounds": [
            {"year": 2019, "month_of_year": 0},
            {"year": 2019, "month_of_year": 13},
            {"year": 2019, "month_of_year": 1, "day_of_month": 0},
            {"year": 2019, "month_of_year": 1, "day_of_month": 32},
            {"year": 2019, "month_of_year": 2, "day_of_month": 29},
            {"truncated": True, "month_of_year": 1, "day_of_month": 32},

            {"year": 2019, "week_of_year": 0},
            {"year": 2019, "week_of_year": 53},
            {"year": 2019, "week_of_year": 1, "day_of_week": 0},
            {"year": 2019, "week_of_year": 1, "day_of_week": 8},

            {"year": 2019, "day_of_year": 0},
            {"year": 2019, "day_of_year": 366},

            {"year": 2019, "hour_of_day": -1},
            {"year": 2019, "hour_of_day": 25},
            {"year": 2019, "hour_of_day": 10, "hour_of_day_decimal": -0.1},
            {"year": 2019, "hour_of_day": 10, "hour_of_day_decimal": 1},
            {"year": 2019, "hour_of_day": 24, "hour_of_day_decimal": 0.1},

            {"year": 2019, "hour_of_day": 10, "minute_of_hour": -1},
            {"year": 2019, "hour_of_day": 10, "minute_of_hour": 60},
            {"year": 2019, "hour_of_day": 24, "minute_of_hour": 1},
            {"year": 2019, "hour_of_day": 10, "minute_of_hour": 1,
             "minute_of_hour_decimal": -0.1},
            {"year": 2019, "hour_of_day": 10, "minute_of_hour": 1,
             "minute_of_hour_decimal": 1},

            {"year": 2019, "hour_of_day": 10, "minute_of_hour": 1,
             "second_of_minute": -1},
            {"year": 2019, "hour_of_day": 10, "minute_of_hour": 1,
             "second_of_minute": 60},
            {"year": 2019, "hour_of_day": 24, "minute_of_hour": 1,
             "second_of_minute": 1},
            {"year": 2019, "hour_of_day": 10, "minute_of_hour": 1,
             "second_of_minute": 1, "second_of_minute_decimal": -0.1},
            {"year": 2019, "hour_of_day": 10, "minute_of_hour": 1,
             "second_of_minute": 1, "second_of_minute_decimal": 1},

            {"year": 2019, "time_zone_hour": -100},
            {"year": 2019, "time_zone_hour": 100},
            {"year": 2019, "time_zone_hour": 0, "time_zone_minute": -60},
            {"year": 2019, "time_zone_hour": 1, "time_zone_minute": -1},
            {"year": 2019, "time_zone_hour": 1, "time_zone_minute": 60},
            {"year": 2019, "time_zone_hour": -1, "time_zone_minute": 1}
        ]
    }


def get_timepoint_conflicting_input_tests():
    """Yield tests for checking TimePoints initialized with incompatible
    inputs."""
    return [
        {"year": 2020, "day_of_year": 1, "month_of_year": 1},
        {"year": 2020, "day_of_year": 1, "day_of_month": 1},
        {"year": 2020, "day_of_year": 6, "week_of_year": 2},
        {"year": 2020, "day_of_year": 1, "day_of_week": 3},

        {"year": 2020, "month_of_year": 2, "week_of_year": 5},
        {"year": 2020, "month_of_year": 2, "day_of_week": 6},
        {"year": 2020, "day_of_month": 6, "week_of_year": 2},
        {"year": 2020, "day_of_month": 1, "day_of_week": 3}
    ]


def run_comparison_tests(data_class, test_cases):
    """
    Args:
        data_class: E.g. Duration or TimePoint
        test_cases (dict): Of the form {"==": [...], "<": [...], ...}
    """
    for op in test_cases:
        for case in test_cases[op]:
            lhs = data_class(**case[0])
            rhs = data_class(**case[1])
            expected = {"forward": case[2],
                        "reverse": case[3] if len(case) == 4 else case[2]}
            if op == "==":
                tests = [
                    {"op": "==", "forward": lhs == rhs, "reverse": rhs == lhs}]
                if True in expected.values():
                    tests.append({"op": "<=", "forward": lhs <= rhs,
                                  "reverse": rhs <= lhs})
                    tests.append({"op": ">=", "forward": lhs >= rhs,
                                  "reverse": rhs >= lhs})
            if op == "<":
                tests = [
                    {"op": "<", "forward": lhs < rhs, "reverse": rhs < lhs}]
                if True in expected.values():
                    tests.append({"op": "<=", "forward": lhs <= rhs,
                                  "reverse": rhs <= lhs})
            if op == "<=":
                tests = [
                    {"op": "<=", "forward": lhs <= rhs, "reverse": rhs <= lhs}]
            if op == ">":
                tests = [
                    {"op": ">", "forward": lhs > rhs, "reverse": rhs > lhs}]
                if True in expected.values():
                    tests.append({"op": ">=", "forward": lhs >= rhs,
                                  "reverse": rhs >= lhs})
            if op == ">=":
                tests = [
                    {"op": ">=", "forward": lhs >= rhs, "reverse": rhs >= lhs}]

            for test in tests:
                assert test["forward"] is expected["forward"], (
                    "{0} {1} {2}".format(lhs, test["op"], rhs))
                assert test["reverse"] is expected["reverse"], (
                    "{0} {1} {2}".format(rhs, test["op"], lhs))

            if op == "==":
                test = lhs != rhs
                assert test is not expected["forward"], (
                    "{0} != {1}".format(lhs, rhs))
                test = hash(lhs) == hash(rhs)
                assert test is expected["forward"], (
                    "hash of {0} == hash of {1}".format(rhs, lhs))


class TestDataModel(unittest.TestCase):
    """Test the functionality of data model manipulation."""

    def test_days_in_year_range(self):
        """Test the summing-over-days-in-year-range shortcut code."""
        for start_year in range(-401, 2):
            for end_year in range(start_year, 2):
                test_days = data.get_days_in_year_range(
                    start_year, end_year)
                control_days = 0
                for year in range(start_year, end_year + 1):
                    control_days += data.get_days_in_year(year)
                self.assertEqual(
                    control_days, test_days, "days in %s to %s" % (
                        start_year, end_year)
                )

    def test_timeduration(self):
        """Test the Duration class methods."""
        for test_props, method, method_args, ctrl_results in (
                get_timeduration_tests()):
            duration = data.Duration(**test_props)
            duration_method = getattr(duration, method)
            test_results = duration_method(*method_args)
            self.assertEqual(
                test_results, ctrl_results,
                "%s -> %s(%s)" % (test_props, method, method_args)
            )

    def test_duration_float_args(self):
        """Test that floats passed to Duration() init are handled correctly."""
        for kwarg in ["years", "months", "weeks", "days"]:
            with self.assertRaises(BadInputError):
                data.Duration(**{kwarg: 1.5})
        for kwarg, expected_secs in [("hours", 5400), ("minutes", 90),
                                     ("seconds", 1.5)]:
            self.assertEqual(data.Duration(**{kwarg: 1.5}).get_seconds(),
                             expected_secs)

    def test_duration_in_weeks(self):
        """Test the Duration class when the week arg is supplied."""
        dur = data.Duration(weeks=4)
        self.assertEqual(dur.get_is_in_weeks(), True)

        for kwarg, expected_days in [  # 1 unit of each property + 4 weeks
                ("years", 365 + 28), ("months", 30 + 28), ("days", 1 + 28),
                ("hours", 28), ("minutes", 28), ("seconds", 28)]:
            dur = data.Duration(weeks=4, **{kwarg: 1})
            self.assertFalse(dur.get_is_in_weeks())
            self.assertIsNone(dur.weeks)
            self.assertEqual(dur.get_days_and_seconds()[0], expected_days)

    def test_duration_to_weeks(self):
        """Test converting Duration in days to Duration in weeks"""
        duration_in_days = data.Duration(days=365).to_weeks()
        duration_in_weeks = data.Duration(weeks=52)  # 364 days (!)
        self.assertEqual(duration_in_days.weeks, duration_in_weeks.weeks)

    def test_duration_to_days(self):
        """Test converting Duration in weeks to Duration in days"""
        dur = data.Duration(weeks=4)
        self.assertEqual(dur.to_days().days, 28)

    def test_duration_comparison(self):
        """Test the Duration rich comparison methods and hashing."""
        run_comparison_tests(data.Duration, get_duration_comparison_tests())
        dur = data.Duration(days=1)
        for var in [7, 'foo', (1, 2), data.TimePoint(year=2000)]:
            self.assertFalse(dur == var)
            with self.assertRaises(TypeError):
                dur < var

    def test_timeduration_add_week(self):
        """Test the Duration not in weeks add Duration in weeks."""
        self.assertEqual(
            str(data.Duration(days=7) + data.Duration(weeks=1)),
            "P14D")

    def test_duration_floordiv(self):
        """Test the existing dunder floordir, which will be removed when we
        move to Python 3"""
        duration = data.Duration(years=4, months=4, days=4, hours=4,
                                 minutes=4, seconds=4)
        expected = data.Duration(years=2, months=2, days=2, hours=2,
                                 minutes=2, seconds=2)
        duration //= 2
        self.assertEqual(duration, expected)

    def test_duration_in_weeks_floordiv(self):
        """Test the existing dunder floordir, which will be removed when we
        move to Python 3"""
        duration = data.Duration(weeks=4)
        duration //= 2
        self.assertEqual(2, duration.weeks)

    def test_duration_subtract(self):
        """Test subtracting a duration from a timepoint."""
        for test in get_duration_subtract_tests():
            start_point = data.TimePoint(**test["start"])
            test_duration = data.Duration(**test["duration"])
            end_point = data.TimePoint(**test["result"])
            test_subtract = (start_point - test_duration).to_calendar_date()
            self.assertEqual(test_subtract, end_point,
                             "%s - %s" % (start_point, test_duration))

    def test_timepoint_comparison(self):
        """Test the TimePoint rich comparison methods and hashing."""
        run_comparison_tests(data.TimePoint, get_timepoint_comparison_tests())
        point = data.TimePoint(year=2000)
        for var in [7, 'foo', (1, 2), data.Duration(days=1)]:
            self.assertFalse(point == var)
            with self.assertRaises(TypeError):
                point < var
        # Cannot use "<", ">=" etc truncated TimePoints of different modes:
        day_month_point = data.TimePoint(month_of_year=2, day_of_month=5,
                                         truncated=True)
        ordinal_point = data.TimePoint(day_of_year=36, truncated=True)
        with self.assertRaises(TypeError):  # TODO: should be ValueError?
            day_month_point < ordinal_point

    def test_timepoint_plus_float_time_duration_day_of_month_type(self):
        """Test (TimePoint + Duration).day_of_month is an int."""
        time_point = data.TimePoint(year=2000) + data.Duration(seconds=1.0)
        self.assertEqual(type(time_point.day_of_month), int)

    def test_timepoint_subtract(self):
        """Test subtracting one time point from another."""
        for test_props1, test_props2, ctrl_string in (
                get_timepoint_subtract_tests()):
            point1 = data.TimePoint(**test_props1)
            point2 = data.TimePoint(**test_props2)
            test_string = str(point1 - point2)
            self.assertEqual(test_string, ctrl_string,
                             "%s - %s" % (point1, point2))

    def test_timepoint_add_duration(self):
        """Test adding a duration to a timepoint"""
        seconds_added = 5
        timepoint = data.TimePoint(year=1900, month_of_year=1, day_of_month=1,
                                   hour_of_day=1, minute_of_hour=1)
        duration = data.Duration(seconds=seconds_added)
        t = timepoint + duration
        self.assertEqual(seconds_added, t.second_of_minute)

    def test_timepoint_add_duration_without_minute(self):
        """Test adding a duration to a timepoint"""
        seconds_added = 5
        timepoint = data.TimePoint(year=1900, month_of_year=1, day_of_month=1,
                                   hour_of_day=1)
        duration = data.Duration(seconds=seconds_added)
        t = timepoint + duration
        self.assertEqual(seconds_added, t.second_of_minute)

    def test_timepoint_bounds(self):
        """Test out of bounds TimePoints"""
        tests = get_timepoint_bounds_tests()
        for kwargs in tests["in_bounds"]:
            data.TimePoint(**kwargs)
        for kwargs in tests["out_of_bounds"]:
            with self.assertRaises(BadInputError) as cm:
                data.TimePoint(**kwargs)
            assert "out of bounds" in str(cm.exception)

    def test_timepoint_conflicting_inputs(self):
        """Test TimePoints initialized with incompatible inputs"""
        tests = get_timepoint_conflicting_input_tests()
        for kwargs in tests:
            with self.assertRaises(BadInputError) as cm:
                data.TimePoint(**kwargs)
            assert "Conflicting input" in str(cm.exception)


def test_timepoint_without_year():
    """Test that TimePoints cannot be init'd without a year unless
    truncated"""
    for kwargs in [{}, {"month_of_year": 2}, {"hour_of_day": 9}]:
        with pytest.raises(BadInputError) as exc:
            data.TimePoint(**kwargs)
            assert "Missing input: year" in str(exc.value)
    # If truncated, it's fine:
    data.TimePoint(truncated=True, month_of_year=2)
    # TODO: what about just TimePoint(truncated=True) ?
