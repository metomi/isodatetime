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

import copy
import datetime
from itertools import chain
import unittest
import pytest
from unittest.mock import patch, MagicMock, Mock

from metomi.isodatetime import data
from metomi.isodatetime import dumpers
from metomi.isodatetime import parsers
from metomi.isodatetime import parser_spec
from metomi.isodatetime import timezone
from metomi.isodatetime.exceptions import (
    ISO8601SyntaxError, TimePointDumperBoundsError, BadInputError)


def get_timedurationparser_tests():
    """Yield tests for the duration parser."""
    test_expressions = {
        "P3Y": {"years": 3},
        "P90Y": {"years": 90},
        "P1Y2M": {"years": 1, "months": 2},
        "P20Y2M": {"years": 20, "months": 2},
        "P2M": {"months": 2},
        "P52M": {"months": 52},
        "P20Y10M2D": {"years": 20, "months": 10, "days": 2},
        "P1Y3D": {"years": 1, "days": 3},
        "P4M1D": {"months": 4, "days": 1},
        "P3Y404D": {"years": 3, "days": 404},
        "P30Y2D": {"years": 30, "days": 2},
        "PT6H": {"hours": 6},
        "PT1034H": {"hours": 1034},
        "P3YT4H2M": {"years": 3, "hours": 4, "minutes": 2},
        "P30Y2DT10S": {"years": 30, "days": 2, "seconds": 10},
        "PT2S": {"seconds": 2},
        "PT2.5S": {"seconds": 2.5},
        "PT2,5S": {"seconds": 2.5},
        "PT5.5023H": {"hours": 5.5023},
        "PT5,5023H": {"hours": 5.5023},
        "P5W": {"weeks": 5},
        "P100W": {"weeks": 100},
        "P0004-03-02T01": {"years": 4, "months": 3, "days": 2,
                           "hours": 1},
        "P0004": {"years": 4},
        "P0004-03-00": {"years": 4, "months": 3},
        "P0004-00-78": {"years": 4, "days": 78},
        "P0004-078": {"years": 4, "days": 78},
        "P0004-078T10,5": {"years": 4, "days": 78, "hours": 10.5},
        "P00000020T133702": {"days": 20, "hours": 13, "minutes": 37,
                             "seconds": 2},
        "-P3YT4H2M": {"years": -3, "hours": -4, "minutes": -2},
        "-PT5M": {"minutes": -5},
        "-P7Y": {"years": -7, "hours": 0}
    }
    for expression, ctrl_result in test_expressions.items():
        ctrl_data = str(data.Duration(**ctrl_result))
        yield expression, ctrl_data


def get_timedurationdumper_tests():
    """Yield tests for the duration dumper."""
    test_expressions = {
        "P3Y": {"years": 3},
        "P90Y": {"years": 90},
        "P1Y2M": {"years": 1, "months": 2},
        "P20Y2M": {"years": 20, "months": 2},
        "P2M": {"months": 2},
        "P52M": {"months": 52},
        "P20Y10M2D": {"years": 20, "months": 10, "days": 2},
        "P1Y3D": {"years": 1, "days": 3},
        "P4M1D": {"months": 4, "days": 1},
        "P3Y404D": {"years": 3, "days": 404},
        "P30Y2D": {"years": 30, "days": 2},
        "PT6H": {"hours": 6},
        "PT1034H": {"hours": 1034},
        "P3YT4H2M": {"years": 3, "hours": 4, "minutes": 2},
        "P30Y2DT10S": {"years": 30, "days": 2, "seconds": 10},
        "PT2S": {"seconds": 2},
        "PT2,5S": {"seconds": 2.5},
        "PT5,5023H": {"hours": 5.5023},
        "P5W": {"weeks": 5},
        "P100W": {"weeks": 100},
        "-P3YT4H2M": {"years": -3, "hours": -4, "minutes": -2},
        "-PT5M": {"minutes": -5},
        "-P7Y": {"years": -7, "hours": 0},
        "PT1H": {"seconds": 3600, "standardize": True},
        "P1DT5M": {"minutes": 1445, "standardize": True},
        "PT59S": {"seconds": 59, "standardize": True},
        "PT1H4M56S": {"minutes": 10, "seconds": 3296, "standardize": True},
    }
    for expression, ctrl_result in test_expressions.items():
        yield expression, ctrl_result


def get_timepoint_dumper_tests():
    """Yield tests for custom timepoint dumps."""
    return [
        (
            {"year": 44, "month_of_year": 1, "day_of_month": 4,
             "hour_of_day": 5, "minute_of_hour": 1, "second_of_minute": 2,
             "time_zone_hour": 0, "time_zone_minute": 0},
            [("CCYY-MMDDThhmmZ", "0044-0104T0501Z"),
             ("YYDDDThh:mm:ss", "44004T05:01:02"),
             ("WwwD", "W011"),
             ("CCDDDThh*ss-0600", "00003T23*02-0600"),
             ("+XCCYY-MM-DDThh:mm:ss-11:45",
              "+000044-01-03T17:16:02-11:45"),
             ("+XCCYYMM-DDThh-01:00", "+00004401-04T04-01:00"),
             ("+XCCYYMM-DDThh+13:00", "+00004401-04T18+13:00"),
             ("+XCCYYMM-DDThh-0100", "+00004401-04T04-0100"),
             ("+XCCYYMM-DDThh+1300", "+00004401-04T18+1300"),
             ("+XCCYYMMDDThh-0100", "+0000440104T04-0100"),
             ("+XCCYYMMDDThh+13", "+0000440104T18+13"),
             ("+XCCYYMMDDThh+hhmm", "+0000440104T05+0000"),
             ("+XCCYY-MM-DDThh:mm:ss+hh:mm",
              "+000044-01-04T05:01:02+00:00"),
             ("DD/MM/CCYY is a silly format", "04/01/0044 is a silly format"),
             ("ThhZ", "T05Z"),
             ("%Y-%m-%dT%H:%M", "0044-01-04T05:01"),
             ("CCYYMMDD00.T+3", "0044010400.T+3"),
             ("T+3", "T+3")]
        ),
        (
            {"year": 500200, "month_of_year": 7, "day_of_month": 28,
             "num_expanded_year_digits": 2, "hour_of_day": 0,
             "hour_of_day_decimal": 0.4356, "time_zone_hour": -8,
             "time_zone_minute": -30},
            [("+XCCYY-MMDDThhmmZ", "+500200-0728T0856Z"),
             ("+XCCYYDDDThh:mm:ss", "+500200209T00:26:08"),
             ("WwwD", "W311"),
             ("+XCCDDDThh*ss-0600", "+5002209T02*08-0600"),
             ("+XCCYY-MM-DDThh:mm:ss-11:45",
              "+500200-07-27T21:11:08-11:45"),
             ("+XCCYYMM-DDThhmm-01:00", "+50020007-28T0756-01:00"),
             ("+XCCYYMM-DDThhmm+13:00", "+50020007-28T2156+13:00"),
             ("+XCCYYMM-DDThhmm-0100", "+50020007-28T0756-0100"),
             ("+XCCYYMM-DDThhmm+1300", "+50020007-28T2156+1300"),
             ("+XCCYYMMDDThhmm-0100", "+5002000728T0756-0100"),
             ("+XCCYYMMDDThhmm+13", "+5002000728T2156+13"),
             ("+XCCYYMMDDThh+hhmm", "+5002000728T00-0830"),
             ("+XCCYYWwwDThhmm+hh", "+500200W311T0026-08"),
             ("+XCCYYDDDThhmm+hh", "+500200209T0026-08"),
             ("+XCCYY-MM-DDThh:mm:ss+hh:mm",
              "+500200-07-28T00:26:08-08:30"),
             ("+XCCYY-MM-DDThh:mm:ssZ", "+500200-07-28T08:56:08Z"),
             ("DD/MM/+XCCYY is a silly format",
              "28/07/+500200 is a silly format"),
             ("ThhmmZ", "T0856Z"),
             ("%m-%dT%H:%M", "07-28T00:26"),
             ("+XCCYY-MM-DDThh,ii", "+500200-07-28T00,4356")]
        ),
        (
            {"year": -56, "day_of_year": 318, "num_expanded_year_digits": 2,
             "hour_of_day": 5, "minute_of_hour": 1, "time_zone_hour": 6},
            [("+XCCYY-MMDDThhmmZ", "-000056-1112T2301Z"),
             ("+XCCYYDDDThh:mm:ss", "-000056318T05:01:00"),
             ("WwwD", "W461"),
             ("+XCCDDDThh*ss-0600", "-0000317T17*00-0600"),
             ("+XCCYY-MM-DDThh:mm:ss-11:45",
              "-000056-11-12T11:16:00-11:45"),
             ("+XCCYYMM-DDThhmm-01:00", "-00005611-12T2201-01:00"),
             ("+XCCYYMM-DDThhmm+13:00", "-00005611-13T1201+13:00"),
             ("+XCCYYMM-DDThhmm-0100", "-00005611-12T2201-0100"),
             ("+XCCYYMM-DDThhmm+1300", "-00005611-13T1201+1300"),
             ("+XCCYYMMDDThhmm-0100", "-0000561112T2201-0100"),
             ("+XCCYYMMDDThhmm+13", "-0000561113T1201+13"),
             ("+XCCYYMMDDThh+hhmm", "-0000561113T05+0600"),
             ("+XCCYYWwwDThhmm+hh", "-000056W461T0501+06"),
             ("+XCCYYDDDThhmm+hh", "-000056318T0501+06"),
             ("+XCCYY-MM-DDThh:mm:ss+hh:mm",
              "-000056-11-13T05:01:00+06:00"),
             ("+XCCYY-MM-DDThh:mm:ssZ", "-000056-11-12T23:01:00Z"),
             ("DD/MM/+XCCYY is a silly format",
              "13/11/-000056 is a silly format"),
             ("ThhmmZ", "T2301Z"),
             ("%m-%dT%H:%M", "11-13T05:01")]
        ),
        (
            {"year": 1000, "week_of_year": 1, "day_of_week": 1,
             "time_zone_hour": 0},
            [("CCYY-MMDDThhmmZ", "0999-1230T0000Z"),
             ("CCYY-DDDThhmmZ", "0999-364T0000Z"),
             ("CCYY-Www-DThhmm+0200", "1000-W01-1T0200+0200"),
             ("CCYY-Www-DThhmm-0200", "0999-W52-7T2200-0200"),
             ("%Y-%m-%dT%H:%M", "0999-12-30T00:00")]
        ),
        (
            {"year": 999, "day_of_year": 364, "time_zone_hour": 0},
            [("CCYY-MMDDThhmmZ", "0999-1230T0000Z"),
             ("CCYY-DDDThhmmZ", "0999-364T0000Z"),
             ("CCYY-Www-DThhmm+0200", "1000-W01-1T0200+0200"),
             ("CCYY-Www-DThhmm-0200", "0999-W52-7T2200-0200"),
             ("%Y-%m-%dT%H:%M", "0999-12-30T00:00")]
        ),
        (
            {"year": 2027, "month_of_year": 12, "day_of_month": 31,
             "minute_of_hour": 59, "minute_of_hour_decimal": 0.99999999},
            [("CCYY-MM-DDThh:mm,nnZ", "2027-12-31T00:59,999999Z"),
             ("CCYY-MM-DDThh:mm.nnZ", "2027-12-31T00:59.999999Z"),
             ("Thh:mm:ss,tt", "T00:59:59,999999")]
        )
    ]


def get_timepointdumper_failure_tests():
    """Yield tests that raise exceptions for custom time point dumps."""
    bounds_error = TimePointDumperBoundsError
    return [
        (
            {"year": 10000, "month_of_year": 1, "day_of_month": 4,
             "time_zone_hour": 0, "time_zone_minute": 0},
            [("CCYY-MMDDThhmmZ", bounds_error, 0),
             ("%Y-%m-%dT%H:%M", bounds_error, 0)]
        ),
        (
            {"year": -10000, "month_of_year": 1, "day_of_month": 4,
             "time_zone_hour": 0, "time_zone_minute": 0},
            [("CCYY-MMDDThhmmZ", bounds_error, 0),
             ("%Y-%m-%dT%H:%M", bounds_error, 0)]
        ),
        (
            {"year": 10000, "month_of_year": 1, "day_of_month": 4,
             "time_zone_hour": 0, "time_zone_minute": 0},
            [("CCYY-MMDDThhmmZ", bounds_error, 2)]
        ),
        (
            {"year": -10000, "month_of_year": 1, "day_of_month": 4,
             "time_zone_hour": 0, "time_zone_minute": 0},
            [("CCYY-MMDDThhmmZ", bounds_error, 2)]
        ),
        (
            {"year": 1000000, "month_of_year": 1, "day_of_month": 4,
             "time_zone_hour": 0, "time_zone_minute": 0},
            [("+XCCYY-MMDDThhmmZ", bounds_error, 2)]
        ),
        (
            {"year": -1000000, "month_of_year": 1, "day_of_month": 4,
             "time_zone_hour": 0, "time_zone_minute": 0},
            [("+XCCYY-MMDDThhmmZ", bounds_error, 2)]
        )
    ]


def get_timepointparser_tests(allow_only_basic=False,
                              allow_truncated=False,
                              skip_time_zones=False):
    """Yield tests for the time point parser."""
    # Note: test dates assume 2 expanded year digits.
    test_date_map = {
        "basic": {
            "complete": {
                "00440104": {"year": 44, "month_of_year": 1,
                             "day_of_month": 4},
                "+5002000830": {"year": 500200, "month_of_year": 8,
                                "day_of_month": 30,
                                "num_expanded_year_digits": 2},
                "-0000561113": {"year": -56, "month_of_year": 11,
                                "day_of_month": 13,
                                "num_expanded_year_digits": 2},
                "-1000240210": {"year": -100024, "month_of_year": 2,
                                "day_of_month": 10,
                                "num_expanded_year_digits": 2},
                "1967056": {"year": 1967, "day_of_year": 56},
                "+123456078": {"year": 123456, "day_of_year": 78,
                               "num_expanded_year_digits": 2},
                "-004560134": {"year": -4560, "day_of_year": 134,
                               "num_expanded_year_digits": 2},
                "1001W011": {"year": 1001, "week_of_year": 1,
                             "day_of_week": 1},
                "+000001W457": {"year": 1, "week_of_year": 45,
                                "day_of_week": 7,
                                "num_expanded_year_digits": 2},
                "-010001W053": {"year": -10001, "week_of_year": 5,
                                "day_of_week": 3,
                                "num_expanded_year_digits": 2}
            },
            "reduced": {
                "4401-03": {"year": 4401, "month_of_year": 3},
                "1982": {"year": 1982},
                "19": {"year": 1900},
                "+056789-01": {"year": 56789, "month_of_year": 1,
                               "num_expanded_year_digits": 2},
                "-000001-12": {"year": -1, "month_of_year": 12,
                               "num_expanded_year_digits": 2},
                "-789123": {"year": -789123, "num_expanded_year_digits": 2},
                "+450001": {"year": 450001, "num_expanded_year_digits": 2},
                # The following cannot be parsed - looks like truncated -YYMM.
                #  "-0023": {"year": -2300, "num_expanded_year_digits": 2},
                "+5678": {"year": 567800, "num_expanded_year_digits": 2},
                "1765W04": {"year": 1765, "week_of_year": 4},
                "+001765W44": {"year": 1765, "week_of_year": 44,
                               "num_expanded_year_digits": 2},
                "-123321W50": {"year": -123321, "week_of_year": 50,
                               "num_expanded_year_digits": 2}
            },
            "truncated": {
                "-9001": {"year": 90, "month_of_year": 1,
                          "truncated": True,
                          "truncated_property": "year_of_century"},
                "960328": {"year": 96, "month_of_year": 3,
                           "day_of_month": 28,
                           "truncated": True,
                           "truncated_property": "year_of_century"},
                "-90": {"year": 90, "truncated": True,
                        "truncated_property": "year_of_century"},
                "--0501": {"month_of_year": 5, "day_of_month": 1,
                           "truncated": True},
                "--12": {"month_of_year": 12, "truncated": True},
                "---30": {"day_of_month": 30, "truncated": True},
                "98354": {"year": 98, "day_of_year": 354, "truncated": True,
                          "truncated_property": "year_of_century"},
                "-034": {"day_of_year": 34, "truncated": True},
                "00W031": {"year": 0, "week_of_year": 3, "day_of_week": 1,
                           "truncated": True,
                           "truncated_property": "year_of_century"},
                "99W34": {"year": 99, "week_of_year": 34, "truncated": True,
                          "truncated_property": "year_of_century"},
                "-1W02": {"year": 1, "week_of_year": 2,
                          "truncated": True,
                          "truncated_property": "year_of_decade"},
                "-W031": {"week_of_year": 3, "day_of_week": 1,
                          "truncated": True},
                "-W32": {"week_of_year": 32, "truncated": True},
                "-W-1": {"day_of_week": 1, "truncated": True}
            }
        },
        "extended": {
            "complete": {
                "0044-01-04": {"year": 44, "month_of_year": 1,
                               "day_of_month": 4},
                "+500200-08-30": {"year": 500200, "month_of_year": 8,
                                  "day_of_month": 30,
                                  "num_expanded_year_digits": 2},
                "-000056-11-13": {"year": -56, "month_of_year": 11,
                                  "day_of_month": 13,
                                  "num_expanded_year_digits": 2},
                "-100024-02-10": {"year": -100024, "month_of_year": 2,
                                  "day_of_month": 10,
                                  "num_expanded_year_digits": 2},
                "1967-056": {"year": 1967, "day_of_year": 56},
                "+123456-078": {"year": 123456, "day_of_year": 78,
                                "num_expanded_year_digits": 2},
                "-004560-134": {"year": -4560, "day_of_year": 134,
                                "num_expanded_year_digits": 2},
                "1001-W01-1": {"year": 1001, "week_of_year": 1,
                               "day_of_week": 1},
                "+000001-W45-7": {"year": 1, "week_of_year": 45,
                                  "day_of_week": 7,
                                  "num_expanded_year_digits": 2},
                "-010001-W05-3": {"year": -10001, "week_of_year": 5,
                                  "day_of_week": 3,
                                  "num_expanded_year_digits": 2}
            },
            "reduced": {
                "4401-03": {"year": 4401, "month_of_year": 3},
                "1982": {"year": 1982},
                "19": {"year": 1900},
                "+056789-01": {"year": 56789, "month_of_year": 1,
                               "num_expanded_year_digits": 2},
                "-000001-12": {"year": -1, "month_of_year": 12,
                               "num_expanded_year_digits": 2},
                "-789123": {"year": -789123, "num_expanded_year_digits": 2},
                "+450001": {"year": 450001, "num_expanded_year_digits": 2},
                # The following cannot be parsed - looks like truncated -YYMM.
                #  "-0023": {"year": -2300, "num_expanded_year_digits": 2},
                "+5678": {"year": 567800, "num_expanded_year_digits": 2},
                "1765-W04": {"year": 1765, "week_of_year": 4},
                "+001765-W44": {"year": 1765, "week_of_year": 44,
                                "num_expanded_year_digits": 2},
                "-123321-W50": {"year": -123321, "week_of_year": 50,
                                "num_expanded_year_digits": 2}
            },
            "truncated": {
                "-9001": {"year": 90, "month_of_year": 1,
                          "truncated": True,
                          "truncated_property": "year_of_century"},
                "96-03-28": {"year": 96, "month_of_year": 3,
                             "day_of_month": 28,
                             "truncated": True,
                             "truncated_property": "year_of_century"},
                "-90": {"year": 90, "truncated": True,
                        "truncated_property": "year_of_century"},
                "--05-01": {"month_of_year": 5, "day_of_month": 1,
                            "truncated": True},
                "--12": {"month_of_year": 12, "truncated": True},
                "---30": {"day_of_month": 30, "truncated": True},
                "98-354": {"year": 98, "day_of_year": 354, "truncated": True,
                           "truncated_property": "year_of_century"},
                "-034": {"day_of_year": 34, "truncated": True},
                "00-W03-1": {"year": 0, "week_of_year": 3, "day_of_week": 1,
                             "truncated": True,
                             "truncated_property": "year_of_century"},
                "99-W34": {"year": 99, "week_of_year": 34, "truncated": True,
                           "truncated_property": "year_of_century"},
                "-1-W02": {"year": 1, "week_of_year": 2,
                           "truncated": True,
                           "truncated_property": "year_of_decade"},
                "-W03-1": {"week_of_year": 3, "day_of_week": 1,
                           "truncated": True},
                "-W32": {"week_of_year": 32, "truncated": True},
                "-W-1": {"day_of_week": 1, "truncated": True}
            }
        }
    }
    test_time_map = {
        "basic": {
            "complete": {
                "050102": {"hour_of_day": 5, "minute_of_hour": 1,
                           "second_of_minute": 2},
                "235902,345": {"hour_of_day": 23, "minute_of_hour": 59,
                               "second_of_minute": 2,
                               "second_of_minute_decimal": 0.345},
                "235902.345": {"hour_of_day": 23, "minute_of_hour": 59,
                               "second_of_minute": 2,
                               "second_of_minute_decimal": 0.345},
                "1201,4": {"hour_of_day": 12, "minute_of_hour": 1,
                           "minute_of_hour_decimal": 0.4},
                "1201.4": {"hour_of_day": 12, "minute_of_hour": 1,
                           "minute_of_hour_decimal": 0.4},
                "00,4356": {"hour_of_day": 0,
                            "hour_of_day_decimal": 0.4356},
                "00.4356": {"hour_of_day": 0,
                            "hour_of_day_decimal": 0.4356}
            },
            "reduced": {
                "0203": {"hour_of_day": 2, "minute_of_hour": 3},
                "17": {"hour_of_day": 17}
            },
            "truncated": {
                "-5612": {"minute_of_hour": 56, "second_of_minute": 12,
                          "truncated": True},
                "-12": {"minute_of_hour": 12, "truncated": True},
                "--45": {"second_of_minute": 45, "truncated": True},
                "-1234,45": {"minute_of_hour": 12, "second_of_minute": 34,
                             "second_of_minute_decimal": 0.45,
                             "truncated": True},
                "-1234.45": {"minute_of_hour": 12, "second_of_minute": 34,
                             "second_of_minute_decimal": 0.45,
                             "truncated": True},
                "-34,2": {"minute_of_hour": 34, "minute_of_hour_decimal": 0.2,
                          "truncated": True},
                "-34.2": {"minute_of_hour": 34, "minute_of_hour_decimal": 0.2,
                          "truncated": True},
                "--59,99": {"second_of_minute": 59,
                            "second_of_minute_decimal": 0.99,
                            "truncated": True},
                "--59.99": {"second_of_minute": 59,
                            "second_of_minute_decimal": 0.99,
                            "truncated": True}
            }
        },
        "extended": {
            "complete": {
                "05:01:02": {"hour_of_day": 5, "minute_of_hour": 1,
                             "second_of_minute": 2},
                "23:59:02,345": {"hour_of_day": 23, "minute_of_hour": 59,
                                 "second_of_minute": 2,
                                 "second_of_minute_decimal": 0.345},
                "23:59:02.345": {"hour_of_day": 23, "minute_of_hour": 59,
                                 "second_of_minute": 2,
                                 "second_of_minute_decimal": 0.345},
                "12:01,4": {"hour_of_day": 12, "minute_of_hour": 1,
                            "minute_of_hour_decimal": 0.4},
                "12:01.4": {"hour_of_day": 12, "minute_of_hour": 1,
                            "minute_of_hour_decimal": 0.4},
                "00,4356": {"hour_of_day": 0, "hour_of_day_decimal": 0.4356},
                "00.4356": {"hour_of_day": 0, "hour_of_day_decimal": 0.4356}
            },
            "reduced": {
                "02:03": {"hour_of_day": 2, "minute_of_hour": 3},
                "17": {"hour_of_day": 17}
            },
            "truncated": {
                "-56:12": {"minute_of_hour": 56, "second_of_minute": 12,
                           "truncated": True},
                "-12": {"minute_of_hour": 12, "truncated": True},
                "--45": {"second_of_minute": 45, "truncated": True},
                "-12:34,45": {"minute_of_hour": 12, "second_of_minute": 34,
                              "second_of_minute_decimal": 0.45,
                              "truncated": True},
                "-12:34.45": {"minute_of_hour": 12, "second_of_minute": 34,
                              "second_of_minute_decimal": 0.45,
                              "truncated": True},
                "-34,2": {"minute_of_hour": 34, "minute_of_hour_decimal": 0.2,
                          "truncated": True},
                "-34.2": {"minute_of_hour": 34, "minute_of_hour_decimal": 0.2,
                          "truncated": True},
                "--59,99": {"second_of_minute": 59,
                            "second_of_minute_decimal": 0.99,
                            "truncated": True},
                "--59.99": {"second_of_minute": 59,
                            "second_of_minute_decimal": 0.99,
                            "truncated": True}
            }
        }
    }
    test_time_zone_map = {
        "basic": {
            "Z": {"time_zone_hour": 0, "time_zone_minute": 0},
            "+01": {"time_zone_hour": 1},
            "-05": {"time_zone_hour": -5},
            "+2301": {"time_zone_hour": 23, "time_zone_minute": 1},
            "-1230": {"time_zone_hour": -12, "time_zone_minute": -30}
        },
        "extended": {
            "Z": {"time_zone_hour": 0, "time_zone_minute": 0},
            "+01": {"time_zone_hour": 1},
            "-05": {"time_zone_hour": -5},
            "+23:01": {"time_zone_hour": 23, "time_zone_minute": 1},
            "-12:30": {"time_zone_hour": -12, "time_zone_minute": -30}
        }
    }
    format_ok_keys = ["basic", "extended"]
    if allow_only_basic:
        format_ok_keys = ["basic"]
    date_combo_ok_keys = ["complete"]
    if allow_truncated:
        date_combo_ok_keys = ["complete", "truncated"]
    time_combo_ok_keys = ["complete", "reduced"]
    time_designator = parser_spec.TIME_DESIGNATOR
    for format_type in format_ok_keys:
        date_format_tests = test_date_map[format_type]
        time_format_tests = test_time_map[format_type]
        time_zone_format_tests = test_time_zone_map[format_type]
        for date_key in date_format_tests:
            if not allow_truncated and date_key == "truncated":
                continue
            for date_expr, info in date_format_tests[date_key].items():
                yield date_expr, info
        for date_key in date_combo_ok_keys:
            date_tests = date_format_tests[date_key]
            # Add a blank date for time-only testing.
            for date_expr, info in date_tests.items():
                for time_key in time_combo_ok_keys:
                    time_items = time_format_tests[time_key].items()
                    for time_expr, time_info in time_items:
                        combo_expr = (
                            date_expr +
                            time_designator +
                            time_expr
                        )
                        combo_info = {}
                        for key, value in chain(
                                info.items(), time_info.items()):
                            combo_info[key] = value
                        yield combo_expr, combo_info
                        if skip_time_zones:
                            continue
                        time_zone_items = time_zone_format_tests.items()
                        for time_zone_expr, time_zone_info in time_zone_items:
                            tz_expr = combo_expr + time_zone_expr
                            tz_info = {}
                            for key, value in \
                                chain(combo_info.items(),
                                      time_zone_info.items()):
                                tz_info[key] = value
                            yield tz_expr, tz_info
        if not allow_truncated:
            continue
        for time_key in time_format_tests:
            time_tests = time_format_tests[time_key]
            for time_expr, time_info in time_tests.items():
                combo_expr = (
                    time_designator +
                    time_expr
                )
                # Add truncated (no date).
                combo_info = {"truncated": True}
                for key, value in time_info.items():
                    combo_info[key] = value
                yield combo_expr, combo_info
                if skip_time_zones:
                    continue
                time_zone_items = time_zone_format_tests.items()
                for time_zone_expr, time_zone_info in time_zone_items:
                    tz_expr = combo_expr + time_zone_expr
                    tz_info = {}
                    for key, value in \
                        chain(combo_info.items(),
                              time_zone_info.items()):
                        tz_info[key] = value
                    yield tz_expr, tz_info


def get_truncated_property_tests():
    """Tests for largest truncated and smallest missing property names."""
    test_timepoints = {
        "-9001": {"year": 90,
                  "month_of_year": 1,
                  "largest_truncated_property_name": "year_of_century",
                  "smallest_missing_property_name": "century"},
        "20960328": {"year": 96,
                     "month_of_year": 3,
                     "day_of_month": 28,
                     "largest_truncated_property_name": None,
                     "smallest_missing_property_name": None},
        "-90": {"year": 90,
                "largest_truncated_property_name": "year_of_century",
                "smallest_missing_property_name": "century"},
        "--0501": {"month_of_year": 5, "day_of_month": 1,
                   "largest_truncated_property_name": "month_of_year",
                   "smallest_missing_property_name": "year_of_century"},
        "--12": {"month_of_year": 12,
                 "largest_truncated_property_name": "month_of_year",
                 "smallest_missing_property_name": "year_of_century"},
        "---30": {"day_of_month": 30,
                  "largest_truncated_property_name": "day_of_month",
                  "smallest_missing_property_name": "month_of_year"},
        "98354": {"year": 98,
                  "day_of_year": 354,
                  "largest_truncated_property_name": "year_of_century",
                  "smallest_missing_property_name": "century"},
        "-034": {"day_of_year": 34,
                 "largest_truncated_property_name": "day_of_year",
                 "smallest_missing_property_name": "year_of_century"},
        "00W031": {"year": 0,
                   "week_of_year": 3,
                   "day_of_week": 1,
                   "largest_truncated_property_name": "year_of_century",
                   "smallest_missing_property_name": "century"},
        "99W34": {"year": 99,
                  "week_of_year": 34,
                  "largest_truncated_property_name": "year_of_century",
                  "smallest_missing_property_name": "century"},
        "-1W02": {"year": 1,
                  "week_of_year": 2,
                  "largest_truncated_property_name": "year_of_decade",
                  "smallest_missing_property_name": "decade_of_century"},
        "-W031": {"week_of_year": 3,
                  "day_of_week": 1,
                  "largest_truncated_property_name": "week_of_year",
                  "smallest_missing_property_name": "year_of_century"},
        "-W32": {"week_of_year": 32,
                 "largest_truncated_property_name": "week_of_year",
                 "smallest_missing_property_name": "year_of_century"},
        "-W-1": {"day_of_week": 1,
                 "largest_truncated_property_name": "day_of_week",
                 "smallest_missing_property_name": "week_of_year"},
        "T04:30": {"hour_of_day": 4,
                   "minute_of_hour": 30,
                   "largest_truncated_property_name": "hour_of_day",
                   "smallest_missing_property_name": "day_of_month"},
        "T19": {"hour_of_day": 19,
                "largest_truncated_property_name": "hour_of_day",
                "smallest_missing_property_name": "day_of_month"},
        "T-56:12": {"minute_of_hour": 56,
                    "second_of_minute": 12,
                    "largest_truncated_property_name": "minute_of_hour",
                    "smallest_missing_property_name": "hour_of_day"},
        "T-12": {"minute_of_hour": 12,
                 "largest_truncated_property_name": "minute_of_hour",
                 "smallest_missing_property_name": "hour_of_day"},
        "T--45": {"second_of_minute": 45,
                  "largest_truncated_property_name": "second_of_minute",
                  "smallest_missing_property_name": "minute_of_hour"},
        "T-12:34.45": {"minute_of_hour": 12,
                       "second_of_minute": 34,
                       "second_of_minute_decimal": 0.45,
                       "largest_truncated_property_name": "minute_of_hour",
                       "smallest_missing_property_name": "hour_of_day"},
        "T-34,2": {"minute_of_hour": 34,
                   "minute_of_hour_decimal": 0.2,
                   "largest_truncated_property_name": "minute_of_hour",
                   "smallest_missing_property_name": "hour_of_day"},
        "T--59.99": {"second_of_minute": 59,
                     "second_of_minute_decimal": 0.99,
                     "largest_truncated_property_name": "second_of_minute",
                     "smallest_missing_property_name": "minute_of_hour"}}
    return test_timepoints


def get_timerecurrence_expansion_tests():
    """Return test expansion expressions for data.TimeRecurrence.

    If no. of repetitions is unbounded, will test the first three.
    """
    return [
        ("R5/2020-01-01T00:00:00Z/2020-01-05T00:00:00Z",
         ["2020-01-01T00:00:00Z", "2020-01-05T00:00:00Z",
          "2020-01-09T00:00:00Z", "2020-01-13T00:00:00Z",
          "2020-01-17T00:00:00Z"]),
        ("R3/1001-W01-1T00:00:00Z/1002-W52-6T00:00:00-05:30",
         ["1001-W01-1T00:00:00Z", "1002-W52-6T05:30:00Z",
          "1005-W01-4T11:00:00Z"]),
        ("R3/P700D/1957-W01-1T06,5Z",
         ["1953-W10-1T06,5Z", "1955-W05-1T06,5Z", "1957-W01-1T06,5Z"]),
        ("R3/P5DT2,5S/1001-W11-1T00:30:02,5-02:00",
         ["1001-W09-5T00:29:57,5-02:00", "1001-W10-3T00:30:00-02:00",
          "1001-W11-1T00:30:02,5-02:00"]),
        ("R/+000001W457T060000Z/P4M1D",
         ["+000001-W45-7T06:00:00Z", "+000002-W11-2T06:00:00Z",
          "+000002-W28-6T06:00:00Z"]),
        ("R/P4M1DT6M/+002302-002T06:00:00-00:30",
         ["+002302-002T06:00:00-00:30", "+002301-244T05:54:00-00:30",
          "+002301-120T05:48:00-00:30"]),
        ("R/P30Y2DT15H/-099994-02-12T17:00:00-02:30",
         ["-099994-02-12T17:00:00-02:30", "-100024-02-10T02:00:00-02:30",
          "-100054-02-07T11:00:00-02:30"]),
        ("R/-100024-02-10T17:00:00-12:30/PT5.5H",
         ["-100024-02-10T17:00:00-12:30", "-100024-02-10T22:30:00-12:30",
          "-100024-02-11T04:00:00-12:30"])
    ]


def get_timerecurrence_comparison_tests():
    """Yield tests for executing the '==' operator and hash() on
    TimeRecurrences."""
    return [
        ("R5/2020-036T00Z/PT15M", "R5/2020-036T00Z/PT15M", True),
        *[("R5/2020-036T00Z/PT15M", rhs, False) for rhs in (
            "R4/2020-036T00Z/PT15M",
            "R5/2020-036T01Z/PT15M",
            "R5/2020-036T00Z/PT14M")],
        # Format 3 vs 4:
        ("R4/2020-01-01T00Z/P1D", "R4/P1D/2020-01-04T00Z", True),
        ("R/2020-01-01T00Z/P1D", "R/P1D/2020-01-04T00Z", False),
        # Format 1 vs 3:
        ("R5/2020-001T00Z/2020-005T00Z", "R5/2020-001T00Z/P4D", True),
        ("R/2020-02-07T09Z/2020-02-07T10Z", "R/2020-02-07T09Z/PT1H", True),
        # Format 1 vs 4:
        ("R5/2020-001T00Z/2020-005T00Z", "R5/P4D/2020-005T00Z", False),
        ("R5/2020-001T00Z/2020-005T00Z", "R5/P4D/2020-017T00Z", True),
        ("R/2020-02-07T09Z/2020-02-07T10Z", "R/PT1H/2020-02-07T10Z", False),
        # Mixed stuff:
        ("R3/2020-05-01T16Z/PT3H", "R3/2020-W18-5T18:30+02:30/PT180M", True),
        # Start point == end point == one repetition:
        ("R27/2020-10-08T00Z/2020-10-08T04+04",
         "R1/2020-10-08T00Z/2020-10-08T00Z", True)
    ]


def get_timerecurrence_expansion_tests_for_alt_calendar(calendar_mode):
    """Return alternate calendar tests for data.TimeRecurrence."""
    if calendar_mode == "360":
        return get_timerecurrence_expansion_tests_360()
    if calendar_mode == "365":
        return get_timerecurrence_expansion_tests_365()
    if calendar_mode == "366":
        return get_timerecurrence_expansion_tests_366()


def get_timerecurrence_expansion_tests_360():
    """Return test expansion expressions for data.TimeRecurrence."""
    return [
        ("R13/1984-01-30T00Z/P1M",
         ["1984-01-30T00:00:00Z", "1984-02-30T00:00:00Z",
          "1984-03-30T00:00:00Z", "1984-04-30T00:00:00Z",
          "1984-05-30T00:00:00Z", "1984-06-30T00:00:00Z",
          "1984-07-30T00:00:00Z", "1984-08-30T00:00:00Z",
          "1984-09-30T00:00:00Z", "1984-10-30T00:00:00Z",
          "1984-11-30T00:00:00Z", "1984-12-30T00:00:00Z",
          "1985-01-30T00:00:00Z"]),
        ("R2/1984-01-30T00Z/P1D",
         ["1984-01-30T00:00:00Z", "1984-02-01T00:00:00Z"]),
        ("R2/P1D/1984-02-01T00Z",
         ["1984-01-30T00:00:00Z", "1984-02-01T00:00:00Z"]),
        ("R2/P1D/1984-01-01T00Z",
         ["1983-12-30T00:00:00Z", "1984-01-01T00:00:00Z"]),
        ("R2/1983-12-30T00Z/P1D",
         ["1983-12-30T00:00:00Z", "1984-01-01T00:00:00Z"]),
        ("R2/P1D/2005-01-01T00Z",
         ["2004-12-30T00:00:00Z", "2005-01-01T00:00:00Z"]),
        ("R2/2003-12-30T00Z/P1D",
         ["2003-12-30T00:00:00Z", "2004-01-01T00:00:00Z"]),
        ("R2/P1D/2004-01-01T00Z",
         ["2003-12-30T00:00:00Z", "2004-01-01T00:00:00Z"]),
        ("R2/2004-12-30T00Z/P1D",
         ["2004-12-30T00:00:00Z", "2005-01-01T00:00:00Z"]),
        ("R3/P1Y/2005-02-30T00Z",
         ["2003-02-30T00:00:00Z", "2004-02-30T00:00:00Z",
          "2005-02-30T00:00:00Z"]),
        ("R3/2003-02-30T00Z/P1Y",
         ["2003-02-30T00:00:00Z", "2004-02-30T00:00:00Z",
          "2005-02-30T00:00:00Z"]),
    ]


def get_timerecurrence_expansion_tests_365():
    """Return test expansion expressions for data.TimeRecurrence."""
    return [
        ("R13/1984-01-30T00Z/P1M",
         ["1984-01-30T00:00:00Z", "1984-02-28T00:00:00Z",
          "1984-03-28T00:00:00Z", "1984-04-28T00:00:00Z",
          "1984-05-28T00:00:00Z", "1984-06-28T00:00:00Z",
          "1984-07-28T00:00:00Z", "1984-08-28T00:00:00Z",
          "1984-09-28T00:00:00Z", "1984-10-28T00:00:00Z",
          "1984-11-28T00:00:00Z", "1984-12-28T00:00:00Z",
          "1985-01-28T00:00:00Z"]),
        ("R13/1985-01-30T00Z/P1M",
         ["1985-01-30T00:00:00Z", "1985-02-28T00:00:00Z",
          "1985-03-28T00:00:00Z", "1985-04-28T00:00:00Z",
          "1985-05-28T00:00:00Z", "1985-06-28T00:00:00Z",
          "1985-07-28T00:00:00Z", "1985-08-28T00:00:00Z",
          "1985-09-28T00:00:00Z", "1985-10-28T00:00:00Z",
          "1985-11-28T00:00:00Z", "1985-12-28T00:00:00Z",
          "1986-01-28T00:00:00Z"]),
        ("R2/1984-01-30T00Z/P1D",
         ["1984-01-30T00:00:00Z", "1984-01-31T00:00:00Z"]),
        ("R2/P1D/1984-02-01T00Z",
         ["1984-01-31T00:00:00Z", "1984-02-01T00:00:00Z"]),
        ("R2/P1D/1984-01-01T00Z",
         ["1983-12-31T00:00:00Z", "1984-01-01T00:00:00Z"]),
        ("R2/1983-12-30T00Z/P1D",
         ["1983-12-30T00:00:00Z", "1983-12-31T00:00:00Z"]),
        ("R2/2000-02-28T00Z/P1Y1D",
         ["2000-02-28T00:00:00Z", "2001-03-01T00:00:00Z"]),
        ("R2/2001-02-28T00Z/P1Y1D",
         ["2001-02-28T00:00:00Z", "2002-03-01T00:00:00Z"]),
    ]


def get_timerecurrence_expansion_tests_366():
    """Return test expansion expressions for data.TimeRecurrence."""
    return [
        ("R13/1984-01-30T00Z/P1M",
         ["1984-01-30T00:00:00Z", "1984-02-29T00:00:00Z",
          "1984-03-29T00:00:00Z", "1984-04-29T00:00:00Z",
          "1984-05-29T00:00:00Z", "1984-06-29T00:00:00Z",
          "1984-07-29T00:00:00Z", "1984-08-29T00:00:00Z",
          "1984-09-29T00:00:00Z", "1984-10-29T00:00:00Z",
          "1984-11-29T00:00:00Z", "1984-12-29T00:00:00Z",
          "1985-01-29T00:00:00Z"]),
        ("R13/1985-01-30T00Z/P1M",
         ["1985-01-30T00:00:00Z", "1985-02-29T00:00:00Z",
          "1985-03-29T00:00:00Z", "1985-04-29T00:00:00Z",
          "1985-05-29T00:00:00Z", "1985-06-29T00:00:00Z",
          "1985-07-29T00:00:00Z", "1985-08-29T00:00:00Z",
          "1985-09-29T00:00:00Z", "1985-10-29T00:00:00Z",
          "1985-11-29T00:00:00Z", "1985-12-29T00:00:00Z",
          "1986-01-29T00:00:00Z"]),
        ("R2/1984-01-30T00Z/P1D",
         ["1984-01-30T00:00:00Z", "1984-01-31T00:00:00Z"]),
        ("R2/P1D/1984-02-01T00Z",
         ["1984-01-31T00:00:00Z", "1984-02-01T00:00:00Z"]),
        ("R2/P1D/1984-01-01T00Z",
         ["1983-12-31T00:00:00Z", "1984-01-01T00:00:00Z"]),
        ("R2/1983-12-30T00Z/P1D",
         ["1983-12-30T00:00:00Z", "1983-12-31T00:00:00Z"]),
        ("R2/1999-02-28T00Z/P1Y1D",
         ["1999-02-28T00:00:00Z", "2000-02-29T00:00:00Z"]),
        ("R2/2000-02-28T00Z/P1Y1D",
         ["2000-02-28T00:00:00Z", "2001-02-29T00:00:00Z"]),
        ("R2/2001-02-28T00Z/P1Y1D",
         ["2001-02-28T00:00:00Z", "2002-02-29T00:00:00Z"]),
    ]


def get_timerecurrence_membership_tests():
    """Return test membership expressions for data.TimeRecurrence."""
    return [
        ("R5/2020-01-01T00:00:00Z/2020-01-05T00:00:00Z",
         [("2020-01-02T00:00:00Z", False),
          ("2020-01-17T00:00:00Z", True),
          ("2020-01-21T00:00:00Z", False)]),
        ("R3/1001-W01-1T00:00:00Z/1002-W52-6T00:00:00-05:30",
         [("1001-W01-1T00:00:00Z", True),
          ("1000-12-29T00:00:00Z", True),
          ("0901-07-08T12:45:00Z", False),
          ("1001-W01-2T00:00:00Z", False),
          ("1001-W53-3T14:45:00Z", False),
          ("1002-W52-6T05:30:00Z", True),
          ("1002-W52-6T03:30:00-02:00", True),
          ("1002-W52-6T07:30:00+02:00", True),
          ("1005-W01-4T11:00:00Z", True),
          ("10030101T00Z", False)]),
        ("R3/P700D/1957-W01-1T06,5Z",
         [("1953-W10-1T06,5Z", True),
          ("1953-03-02T06,5Z", True),
          ("1952-03-02T06,5Z", False),
          ("1955-W05-1T06,5Z", True),
          ("1957-W01-1T06,5Z", True),
          ("1956-366T06,5Z", True),
          ("1956-356T04,5Z", False)]),
    ]


def get_timerecurrenceparser_tests():
    """Yield tests for the time recurrence parser."""
    test_points = ["-100024-02-10T17:00:00-12:30",
                   "+000001-W45-7T06Z", "1001W011",
                   "1955W051T06,5Z", "1999-06-01",
                   "1967-056", "+5002000830T235902,345",
                   "1765-W04"]
    for reps in [None, 1, 2, 3, 10]:
        if reps is None:
            reps_string = ""
        else:
            reps_string = str(reps)
        point_parser = parsers.TimePointParser()
        duration_parser = parsers.DurationParser()
        for point_expr in test_points:
            duration_tests = get_timedurationparser_tests()
            start_point = point_parser.parse(point_expr)
            for duration_expr, _ in duration_tests:
                if duration_expr.startswith("-P"):
                    # Our negative durations are not supported in recurrences.
                    continue
                duration = duration_parser.parse(duration_expr)
                end_point = start_point + duration
                expr_1 = ("R" + reps_string + "/" + str(start_point) +
                          "/" + str(end_point))
                yield expr_1, {"repetitions": reps, "start_point": start_point,
                               "end_point": end_point}
                expr_3 = ("R" + reps_string + "/" + str(start_point) +
                          "/" + str(duration))
                yield expr_3, {"repetitions": reps, "start_point": start_point,
                               "duration": duration}
                expr_4 = ("R" + reps_string + "/" + str(duration) + "/" +
                          str(end_point))
                yield expr_4, {"repetitions": reps, "duration": duration,
                               "end_point": end_point}


def get_local_time_zone_hours_minutes():
    """Provide an independent method of getting the local time zone."""
    utc_offset = datetime.datetime.now() - datetime.datetime.utcnow()
    # datetime.timedelta represents -21 microseconds as -1 day,
    # +86399 seconds, +999979 microseconds. This is not nice.
    utc_offset_seconds = utc_offset.seconds + 86400 * utc_offset.days
    utc_offset_hours = (utc_offset_seconds + 1800) // 3600
    utc_offset_minutes = (
        ((utc_offset_seconds - 3600 * utc_offset_hours) + 30) // 60
    )
    return utc_offset_hours, utc_offset_minutes


class TestSuite(unittest.TestCase):
    """Test the functionality of parsers and data model manipulation."""

    def test_largest_truncated_property_name(self):
        """Test the largest truncated property name."""

        parser = parsers.TimePointParser(
            allow_truncated=True)

        truncated_property_tests = get_truncated_property_tests()
        for expression in truncated_property_tests.keys():
            try:
                test_data = parser.parse(expression)
            except ISO8601SyntaxError as syn_exc:
                raise ValueError("Parsing failed for {0}: {1}".format(
                    expression, syn_exc))

            self.assertEqual(
                test_data.get_largest_truncated_property_name(),
                truncated_property_tests[expression]
                ["largest_truncated_property_name"],
                msg=expression)

    def test_smallest_missing_property_name(self):
        """Test the smallest missing property name."""

        parser = parsers.TimePointParser(
            allow_truncated=True)

        truncated_property_tests = get_truncated_property_tests()
        for expression in truncated_property_tests.keys():
            try:
                test_data = parser.parse(expression)
            except ISO8601SyntaxError as syn_exc:
                raise ValueError("Parsing failed for {0}: {1}".format(
                    expression, syn_exc))

            self.assertEqual(
                test_data.get_smallest_missing_property_name(),
                truncated_property_tests[expression]
                ["smallest_missing_property_name"],
                msg=expression)

    def test_timeduration_parser(self):
        """Test the duration parsing."""
        parser = parsers.DurationParser()
        for expression, ctrl_result in get_timedurationparser_tests():
            try:
                test_result = str(parser.parse(expression))
            except ISO8601SyntaxError:
                raise ValueError(
                    "DurationParser test failed to parse '%s'" %
                    expression
                )
            self.assertEqual(test_result, ctrl_result, expression)

    def test_timeduration_dumper(self):
        """Test the duration dumping."""
        for ctrl_expression, test_props in get_timedurationdumper_tests():
            duration = data.Duration(**test_props)
            test_expression = str(duration)
            self.assertEqual(test_expression, ctrl_expression,
                             str(test_props))

    def test_timepoint_time_zone(self):
        """Test the time zone handling of timepoint instances."""
        year, month_of_year, day_of_month = (2000, 1, 1)
        utc_offset_hours, utc_offset_minutes = (
            get_local_time_zone_hours_minutes()
        )
        for hour_of_day in range(24):
            for minute_of_hour in [0, 30]:
                point = data.TimePoint(year=year, month_of_year=month_of_year,
                                       day_of_month=day_of_month,
                                       hour_of_day=hour_of_day,
                                       minute_of_hour=minute_of_hour)
                test_dates = [
                    point.to_utc(),
                    point.to_local_time_zone(),
                    point.to_time_zone(data.TimeZone(hours=-13, minutes=-45)),
                    point.to_time_zone(data.TimeZone(hours=8, minutes=30))
                ]
                self.assertEqual(test_dates[0].time_zone.hours, 0,
                                 test_dates[0])
                self.assertEqual(test_dates[0].time_zone.minutes, 0,
                                 test_dates[0])

                self.assertEqual(test_dates[1].time_zone.hours,
                                 utc_offset_hours, test_dates[1])
                self.assertEqual(test_dates[1].time_zone.minutes,
                                 utc_offset_minutes, test_dates[1])

                for i_test_date in list(test_dates):
                    i_test_date_str = str(i_test_date)
                    date_no_tz = i_test_date._copy()
                    date_no_tz._time_zone = data.TimeZone(hours=0, minutes=0)
                    if (i_test_date.time_zone.hours >= 0 or
                            i_test_date.time_zone.minutes >= 0):
                        utc_offset = date_no_tz - i_test_date
                    else:
                        utc_offset = (i_test_date - date_no_tz) * -1
                    self.assertEqual(utc_offset.hours,
                                     i_test_date.time_zone.hours,
                                     i_test_date_str + " utc offset (hrs)")
                    self.assertEqual(utc_offset.minutes,
                                     i_test_date.time_zone.minutes,
                                     i_test_date_str + " utc offset (mins)")
                    for j_test_date in list(test_dates):
                        j_test_date_str = str(j_test_date)
                        self.assertEqual(
                            i_test_date, j_test_date,
                            i_test_date_str + " == " + j_test_date_str)
                        duration = j_test_date - i_test_date
                        self.assertEqual(
                            duration, data.Duration(days=0),
                            i_test_date_str + " - " + j_test_date_str)
        # TODO: test truncated TimePoints

    def test_timepoint_dumper(self):
        """Test the dumping of TimePoint instances."""
        parser = parsers.TimePointParser(allow_truncated=True,
                                         default_to_unknown_time_zone=True)
        dumper = dumpers.TimePointDumper()
        for expression, timepoint_kwargs in get_timepointparser_tests(
                allow_truncated=True):
            ctrl_timepoint = data.TimePoint(**timepoint_kwargs)
            try:
                test_timepoint = parser.parse(str(ctrl_timepoint))
            except ISO8601SyntaxError as syn_exc:
                raise ValueError(
                    "Parsing failed for the dump of {0}: {1}".format(
                        expression, syn_exc))
            self.assertEqual(test_timepoint,
                             ctrl_timepoint, expression)
        for timepoint_kwargs, format_results in (
                get_timepoint_dumper_tests()):
            ctrl_timepoint = data.TimePoint(**timepoint_kwargs)
            for format_, ctrl_data in format_results:
                test_data = dumper.dump(ctrl_timepoint, format_)
                self.assertEqual(test_data, ctrl_data, format_)
        for timepoint_kwargs, format_exception_results in (
                get_timepointdumper_failure_tests()):
            ctrl_timepoint = data.TimePoint(**timepoint_kwargs)
            for format_, ctrl_exception, num_expanded_year_digits in (
                    format_exception_results):
                dumper = dumpers.TimePointDumper(
                    num_expanded_year_digits=num_expanded_year_digits)
                self.assertRaises(ctrl_exception, dumper.dump,
                                  ctrl_timepoint, format_)

    def test_timepoint_dumper_bounds_error_message(self):
        """Test the exception text contains the information expected"""
        the_error = TimePointDumperBoundsError("TimePoint1", "year",
                                               10, 20)
        the_string = the_error.__str__()
        # FIXME:
        self.assertTrue("TimePoint1" in the_string,
                        "Failed to find TimePoint1 in {}".format(the_string))
        self.assertTrue("year" in the_string,
                        "Failed to find TimePoint1 in {}".format(the_string))
        self.assertTrue("10" in the_string,
                        "Failed to find TimePoint1 in {}".format(the_string))
        self.assertTrue("20" in the_string,
                        "Failed to find TimePoint1 in {}".format(the_string))

    get_test_timepoint_dumper_get_time_zone = [
        ["+250:00", None],
        ["+25:00", (25, 0)],
        ["+12:00", (12, 0)],
        ["+12:45", (12, 45)],
        ["+01:00", (1, 0)],
        ["Z", (0, 0)],
        ["-03:00", (-3, 0)],
        ["-03:30", (-3, -30)],
        ["-11:00", (-11, 0)],
        ["+00:00", (0, 0)],
        ["-00:00", (0, 0)]
    ]

    def test_timepoint_dumper_get_time_zone(self):
        """Test the time zone returned by TimerPointDumper.get_time_zone"""
        dumper = dumpers.TimePointDumper(num_expanded_year_digits=2)
        for value, expected in self.get_test_timepoint_dumper_get_time_zone:
            tz = dumper.get_time_zone(value)
            self.assertEqual(expected, tz)

    def test_timepoint_dumper_after_copy(self):
        """Test that printing the TimePoint attributes works after it has
        been copied, see issue #102 for more information"""
        time_point = data.TimePoint(year=2000, truncated=True,
                                    truncated_dump_format='CCYY')
        the_copy = time_point._copy()
        self.assertEqual(str(time_point), str(the_copy))

    def test_timepoint_parser(self):
        """Test the parsing of date/time expressions."""

        # Test unknown time zone assumptions.
        parser = parsers.TimePointParser(
            allow_truncated=True,
            default_to_unknown_time_zone=True)
        for expression, timepoint_kwargs in get_timepointparser_tests(
                allow_truncated=True):
            timepoint_kwargs = copy.deepcopy(timepoint_kwargs)
            try:
                test_data = str(parser.parse(expression))
            except ISO8601SyntaxError as syn_exc:
                raise ValueError("Parsing failed for {0}: {1}".format(
                    expression, syn_exc))
            ctrl_data = str(data.TimePoint(**timepoint_kwargs))
            self.assertEqual(test_data, ctrl_data, expression)
            ctrl_data = expression
            test_data = str(parser.parse(expression, dump_as_parsed=True))
            self.assertEqual(test_data, ctrl_data, expression)

        # Test local time zone assumptions (the default).
        utc_offset_hours, utc_offset_minutes = (
            get_local_time_zone_hours_minutes()
        )
        parser = parsers.TimePointParser(allow_truncated=True)
        for expression, timepoint_kwargs in get_timepointparser_tests(
                allow_truncated=True, skip_time_zones=True):
            timepoint_kwargs = copy.deepcopy(timepoint_kwargs)
            try:
                test_timepoint = parser.parse(expression)
            except ISO8601SyntaxError as syn_exc:
                raise ValueError("Parsing failed for {0}: {1}".format(
                    expression, syn_exc))
            test_data = (test_timepoint.time_zone.hours,
                         test_timepoint.time_zone.minutes)
            ctrl_data = (utc_offset_hours, utc_offset_minutes)
            self.assertEqual(test_data, ctrl_data,
                             "Local time zone for " + expression)

        # Test given time zone assumptions.
        utc_offset_hours, utc_offset_minutes = (
            get_local_time_zone_hours_minutes()
        )
        given_utc_offset_hours = -2  # This is an arbitrary number!
        if given_utc_offset_hours == utc_offset_hours:
            # No point testing this twice, change it.
            given_utc_offset_hours = -3
        given_utc_offset_minutes = -15
        given_time_zone_hours_minutes = (
            given_utc_offset_hours, given_utc_offset_minutes)
        parser = parsers.TimePointParser(
            allow_truncated=True,
            assumed_time_zone=given_time_zone_hours_minutes
        )
        for expression, timepoint_kwargs in get_timepointparser_tests(
                allow_truncated=True, skip_time_zones=True):
            timepoint_kwargs = copy.deepcopy(timepoint_kwargs)
            try:
                test_timepoint = parser.parse(expression)
            except ISO8601SyntaxError as syn_exc:
                raise ValueError("Parsing failed for {0}: {1}".format(
                    expression, syn_exc))
            test_data = (test_timepoint.time_zone.hours,
                         test_timepoint.time_zone.minutes)
            ctrl_data = given_time_zone_hours_minutes
            self.assertEqual(test_data, ctrl_data,
                             "A given time zone for " + expression)

        # Test UTC time zone assumptions.
        parser = parsers.TimePointParser(
            allow_truncated=True,
            assumed_time_zone=(0, 0)
        )
        for expression, timepoint_kwargs in get_timepointparser_tests(
                allow_truncated=True, skip_time_zones=True):
            timepoint_kwargs = copy.deepcopy(timepoint_kwargs)
            try:
                test_timepoint = parser.parse(expression)
            except ISO8601SyntaxError as syn_exc:
                raise ValueError("Parsing failed for {0}: {1}".format(
                    expression, syn_exc))
            test_data = (test_timepoint.time_zone.hours,
                         test_timepoint.time_zone.minutes)
            ctrl_data = (0, 0)
            self.assertEqual(test_data, ctrl_data,
                             "UTC for " + expression)

    def test_timepoint_strftime_strptime(self):
        """Test the strftime/strptime for date/time expressions."""
        parser = parsers.TimePointParser(assumed_time_zone=(0, 0))
        strftime_string = "%d :?foobar++(%F%H %j:%m %M?foobar :%S++(%X %Y:"
        strptime_strings = [
            "%d :?foo++(%H :%m %M?foo :%S++( %Y:",
            "%j :?foo %H++( %M?foo :%S++( %Y:",
            "?foo%s :++("
        ]
        ctrl_date = datetime.datetime(2002, 3, 1, 12, 30, 2,
                                      tzinfo=datetime.timezone.utc)
        test_date = data.TimePoint(
            year=ctrl_date.year,
            month_of_year=ctrl_date.month,
            day_of_month=ctrl_date.day,
            hour_of_day=ctrl_date.hour,
            minute_of_hour=ctrl_date.minute,
            second_of_minute=ctrl_date.second
        )
        # test_date = test_date.to_utc()

        for test_date in [test_date, test_date.to_week_date(),
                          test_date.to_ordinal_date()]:
            # Test strftime (dumping):
            ctrl_data = ctrl_date.strftime(strftime_string)
            test_data = test_date.strftime(strftime_string)
            self.assertEqual(test_data, ctrl_data, strftime_string)

            # Test strptime (parsing):
            for strptime_string in strptime_strings:
                # %s not really supported by datetime
                if "%s" in strptime_string:
                    unix_time = ctrl_date.timestamp()
                    # The `%` below is the string format operator (not modulo)
                    ctrl_dump = strptime_string % int(unix_time)
                    ctrl_data = ctrl_date
                else:
                    ctrl_dump = ctrl_date.strftime(strptime_string)
                    ctrl_data = datetime.datetime.strptime(
                        ctrl_dump, strptime_string)
                test_dump = test_date.strftime(strptime_string)
                test_data = parser.strptime(test_dump, strptime_string)
                test_data = test_data.to_utc()

                self.assertEqual(test_dump, ctrl_dump, strptime_string)

                ctrl_data = (
                    ctrl_data.year, ctrl_data.month, ctrl_data.day,
                    ctrl_data.hour, ctrl_data.minute, ctrl_data.second
                )
                test_data = tuple(list(test_data.get_calendar_date()) +
                                  list(test_data.get_hour_minute_second()))
                self.assertEqual(test_data, ctrl_data,
                                 test_dump + "\n" + strptime_string)

        # Test %z strftime (dumping):
        for sign in [1, -1]:
            for hour in range(0, 24):
                for minute in range(0, 59):
                    if hour == 0 and minute == 0 and sign == -1:
                        # -0000, same as +0000, but invalid.
                        continue
                    test_date = data.TimePoint(
                        year=ctrl_date.year,
                        month_of_year=ctrl_date.month,
                        day_of_month=ctrl_date.day,
                        hour_of_day=ctrl_date.hour,
                        minute_of_hour=ctrl_date.minute,
                        second_of_minute=ctrl_date.second,
                        time_zone_hour=sign * hour,
                        time_zone_minute=sign * minute
                    )
                    ctrl_string = "-" if sign == -1 else "+"
                    ctrl_string += "%02d%02d" % (hour, minute)
                    self.assertEqual(test_date.strftime("%z"),
                                     ctrl_string,
                                     "%z for " + str(test_date))

    def test_timerecurrence_alt_calendars(self):
        """Test recurring date/time series for alternate calendars."""
        for calendar_mode in ["360", "365", "366"]:
            data.CALENDAR.set_mode(calendar_mode + "day")
            self.assertEqual(
                data.CALENDAR.mode,
                getattr(data.Calendar, "MODE_%s" % calendar_mode)
            )
            parser = parsers.TimeRecurrenceParser()
            tests = get_timerecurrence_expansion_tests_for_alt_calendar(
                calendar_mode)
            for expression, ctrl_results in tests:
                try:
                    test_recurrence = parser.parse(expression)
                except ISO8601SyntaxError:
                    raise ValueError(
                        "TimeRecurrenceParser test failed to parse '%s'" %
                        expression
                    )
                test_results = []
                for time_point in test_recurrence:
                    test_results.append(str(time_point))
                self.assertEqual(test_results, ctrl_results,
                                 expression + "(%s)" % calendar_mode)
            data.CALENDAR.set_mode()
            self.assertEqual(data.CALENDAR.mode,
                             data.Calendar.MODE_GREGORIAN)

    def test_timerecurrence(self):
        """Test the recurring date/time series data model."""
        parser = parsers.TimeRecurrenceParser()
        for expression, ctrl_results in get_timerecurrence_expansion_tests():
            try:
                test_recurrence = parser.parse(expression)
            except ISO8601SyntaxError:
                raise ValueError(
                    "TimeRecurrenceParser test failed to parse '%s'" %
                    expression
                )
            test_results = []
            reps = test_recurrence.repetitions or 3
            for i, time_point in enumerate(test_recurrence):
                if i >= reps:
                    break  # Unbounded repetitions, just test 3 of them
                test_results.append(str(time_point))
            self.assertEqual(test_results, ctrl_results, expression)
            if test_recurrence.start_point is None:
                forward_method = test_recurrence.get_prev
                backward_method = test_recurrence.get_next
            else:
                forward_method = test_recurrence.get_next
                backward_method = test_recurrence.get_prev
            test_points = [test_recurrence[0]]
            for i in range(1, reps):
                test_points.append(forward_method(test_points[-1]))
            test_results = [str(point) for point in test_points]
            self.assertEqual(test_results, ctrl_results, expression)
            # Test that going backwards beyond 1st point results in None:
            test_points = [test_recurrence[reps - 1]]
            for i in range(0, reps):
                test_points.append(backward_method(test_points[-1]))
            self.assertEqual(test_points[reps], None, expression)
            # Test backwards method == reverse of forward:
            test_points.pop(-1)
            test_points.reverse()
            test_results = [str(point) for point in test_points]
            self.assertEqual(test_results, ctrl_results, expression)

        for expression, results in get_timerecurrence_membership_tests():
            try:
                test_recurrence = parser.parse(expression)
            except ISO8601SyntaxError:
                raise ValueError(
                    "TimeRecurrenceParser test failed to parse '%s'" %
                    expression
                )
            for timepoint_expression, ctrl_is_member in results:
                timepoint = parsers.parse_timepoint_expression(
                    timepoint_expression)
                test_is_member = test_recurrence.get_is_valid(timepoint)
                self.assertEqual(test_is_member, ctrl_is_member,
                                 timepoint_expression + " in " + expression)

    def test_timerecurrence_parser(self):
        """Test the recurring date/time series parsing."""
        parser = parsers.TimeRecurrenceParser()
        for expression, test_info in get_timerecurrenceparser_tests():
            try:
                test_data = str(parser.parse(expression))
            except ISO8601SyntaxError:
                raise ValueError("Parsing failed for %s" % expression)
            ctrl_data = str(data.TimeRecurrence(**test_info))
            self.assertEqual(test_data, ctrl_data, expression)

    def test_timerecurrence_comparison(self):
        """Test the '==' operator and hash() on TimeRecurrences."""
        parser = parsers.TimeRecurrenceParser()
        tests = get_timerecurrence_comparison_tests()
        for lhs_str, rhs_str, expected in tests:
            lhs = parser.parse(lhs_str)
            rhs = parser.parse(rhs_str)
            test = lhs == rhs
            assert test is expected, "{0} == {1}".format(lhs_str, rhs_str)
            test = rhs == lhs
            assert test is expected, "{0} == {1}".format(rhs_str, lhs_str)
            test = lhs != rhs
            assert test is not expected, "{0} != {1}".format(lhs_str, rhs_str)
            test = hash(lhs) == hash(rhs)
            assert test is expected, (
                "hash of {0} == hash of {1}".format(lhs_str, rhs_str))
            # If recurrences the same, list of timepoints must be equal:
            if lhs.repetitions is not None and rhs.repetitions is not None:
                # Note: don't list() unbounded recurrences!
                test = list(lhs) == list(rhs)
                assert test is expected
        test_recurrence = parser.parse(tests[0][0])
        for var in [7, 'foo', (1, 2), data.Duration(days=1)]:
            self.assertFalse(test_recurrence == var)

    def test_timerecurrence_add(self):
        """Test adding/subtracting Duration to/from TimeRecurrence"""
        rep = 4
        start_pt = data.TimePoint(year=2020, month_of_year=3, day_of_month=13)
        second_pt = data.TimePoint(year=2020, month_of_year=3, day_of_month=20)
        end_pt = data.TimePoint(year=2020, month_of_year=4, day_of_month=3)
        dur = data.Duration(days=7)
        offset = data.Duration(hours=9, minutes=59)

        recurrence_fmt1 = data.TimeRecurrence(
            repetitions=rep, start_point=start_pt, end_point=second_pt)
        recurrence_fmt3 = data.TimeRecurrence(
            repetitions=rep, start_point=start_pt, duration=dur)
        recurrence_fmt4 = data.TimeRecurrence(
            repetitions=rep, duration=dur, end_point=end_pt)
        # Quick check, make sure these equivalent recurrences evaluate as equal
        assert recurrence_fmt1 == recurrence_fmt3 == recurrence_fmt4

        new_start_pt = start_pt + offset
        expected = data.TimeRecurrence(
            repetitions=rep, start_point=new_start_pt, duration=dur)
        for recurrence in (recurrence_fmt1, recurrence_fmt3, recurrence_fmt4):
            assert recurrence + offset == expected
            assert offset + recurrence == expected

        new_start_pt = start_pt - offset
        expected = data.TimeRecurrence(
            repetitions=rep, start_point=new_start_pt, duration=dur)
        for recurrence in (recurrence_fmt1, recurrence_fmt3, recurrence_fmt4):
            assert recurrence - offset == expected

        with pytest.raises(TypeError):
            recurrence_fmt3 + data.TimePoint(year=2049, month_of_year=2)

    def test_invalid_timerecurrence(self):
        """Test that init'ing a TimeRecurrence with bad inputs raises error."""
        start_pt = data.TimePoint(year=2020, day_of_month=9)
        end_pt = data.TimePoint(year=2020, day_of_month=30)
        dur = data.Duration(hours=36)
        _tests = [{"repetitions": 0, "start_point": start_pt, "duration": dur}]
        for reps in (4, None):
            _tests += [
                {"repetitions": reps, "start_point": start_pt,
                 "end_point": end_pt, "duration": dur},
                {"repetitions": reps, "start_point": start_pt},
                {"repetitions": reps, "end_point": end_pt},
                {"repetitions": reps, "duration": dur},
                {"repetitions": reps, "start_point": start_pt,
                 "duration": data.Duration(minutes=-20)},
                {"repetitions": reps, "start_point": end_pt,
                 "end_point": start_pt}
            ]
        for kwargs in _tests:
            with pytest.raises(BadInputError):
                data.TimeRecurrence(**kwargs)

    # data provider for the test test_get_local_time_zone_no_dst
    # the format for the parameters is
    # [tz_seconds, expected_hours, expected_minutes]]
    get_local_time_zone_no_dst = [
        [45900, 12, 45],  # pacific/chatham, +12:45
        [20700, 5, 45],  # asia/kathmandu, +05:45
        [3600, 1, 0],  # arctic/longyearbyen, +01:00
        [0, 0, 0],  # UTC
        [-10800, -3, 0],  # america/sao_paulo, -03:00
        [-12600, -3, 30]  # america/st_johns, -03:30
    ]

    @patch('metomi.isodatetime.timezone.time')
    def test_get_local_time_zone_no_dst(self, mock_time):
        """Test that the hour/minute returned is correct.

        Parts of the time module are mocked so that we can specify scenarios
        without daylight saving time."""
        for tz_seconds, expected_hours, expected_minutes in \
                self.get_local_time_zone_no_dst:
            # for a pre-defined timezone
            mock_time.timezone.__neg__.return_value = tz_seconds
            # time without dst
            mock_time.daylight = False
            # and localtime also without dst
            mock_localtime = Mock()
            mock_time.localtime.return_value = mock_localtime
            mock_localtime.tm_isdst = 0
            hours, minutes = timezone.get_local_time_zone()
            self.assertEqual(expected_hours, hours)
            self.assertEqual(expected_minutes, minutes)

    # data provider for the test test_get_local_time_zone_with_dst
    # the format for the parameters is
    # [tz_seconds, tz_alt_seconds, expected_hours, expected_minutes]
    get_local_time_zone_with_dst = [
        [45900, 49500, 13, 45],  # pacific/chatham, +12:45 and +13:45
        [43200, 46800, 13, 0],  # pacific/auckland, +12:00 and +13:00
        [3600, 7200, 2, 0],  # arctic/longyearbyen, +01:00
        [0, 0, 0, 0],  # UTC
        [-10800, -7200, -2, 0],  # america/sao_paulo, -03:00 and -02:00,
        [-12600, -9000, -2, 30]  # america/st_johns, -03:30 and -02:30
    ]

    @patch('metomi.isodatetime.timezone.time')
    def test_get_local_time_zone_with_dst(self, mock_time):
        """Test that the hour/minute returned is correct

        Parts of the time module are mocked so that we can specify scenarios
        with daylight saving time."""
        for tz_seconds, tz_alt_seconds, expected_hours, expected_minutes in \
                self.get_local_time_zone_with_dst:
            # for a pre-defined timezone
            mock_time.timezone.__neg__.return_value = tz_seconds
            # time without dst
            mock_time.daylight = True
            # and localtime also without dst
            mock_localtime = MagicMock()
            mock_time.localtime.return_value = mock_localtime
            mock_localtime.tm_isdst = 1
            # and with the following alternative time for when dst is set
            mock_time.altzone.__neg__.return_value = tz_alt_seconds
            hours, minutes = timezone.get_local_time_zone()
            self.assertEqual(expected_hours, hours)
            self.assertEqual(expected_minutes, minutes)

    # data provider for the test test_get_local_time_zone_format
    # the format for the parameters is
    # [tz_seconds, tz_format_mode, expected_format]
    get_test_get_local_time_zone_format = [
        # UTC, returns Z, flags are never used for UTC
        [0, timezone.TimeZoneFormatMode.normal, "Z"],
        # Positive values, some with minutes != 0
        # asia/macao, +08:00
        [28800, timezone.TimeZoneFormatMode.normal, "+0800"],
        # asia/macao, +08:00
        [28800, timezone.TimeZoneFormatMode.extended, "+08:00"],
        # asia/macao, +08:00
        [28800, timezone.TimeZoneFormatMode.reduced, "+08"],
        # pacific/chatham, +12:45
        [45900, timezone.TimeZoneFormatMode.normal, "+1245"],
        # pacific/chatham, +12:45
        [45900, timezone.TimeZoneFormatMode.extended, "+12:45"],
        # pacific/chatham, +12:45
        [45900, timezone.TimeZoneFormatMode.reduced, "+1245"],
        # Negative values, some with minutes != 0
        # america/buenos_aires, -03:00
        [-10800, timezone.TimeZoneFormatMode.normal, "-0300"],
        # america/buenos_aires, -03:00
        [-10800, timezone.TimeZoneFormatMode.extended, "-03:00"],
        # america/buenos_aires, -03:00
        [-10800, timezone.TimeZoneFormatMode.reduced, "-03"],
        # america/st_johns, -03:30
        [-12600, timezone.TimeZoneFormatMode.normal, "-0330"],
        # america/st_johns, -03:30
        [-12600, timezone.TimeZoneFormatMode.extended, "-03:30"],
        # america/st_johns, -03:30
        [-12600, timezone.TimeZoneFormatMode.reduced, "-0330"]
    ]

    @patch('metomi.isodatetime.timezone.time')
    def test_get_local_time_zone_format(self, mock_time):
        """Test that the UTC offset string format is correct

        Parts of the time module are mocked so that we can specify scenarios
        with certain timezone seconds offsets. DST is not really
        important for this test case"""
        for tz_seconds, tz_format_mode, expected_format in \
                self.get_test_get_local_time_zone_format:
            # for a pre-defined timezone
            mock_time.timezone.__neg__.return_value = tz_seconds
            # time without dst
            mock_time.daylight = False
            # and localtime also without dst
            mock_localtime = Mock()
            mock_time.localtime.return_value = mock_localtime
            mock_localtime.tm_isdst = 0
            tz_format = timezone.get_local_time_zone_format(tz_format_mode)
            self.assertEqual(expected_format, tz_format)

    def test_timepoint_dump_format(self):
        """Test the timepoint format dump when values are programmatically
        set to None"""
        # TODO: Get rid of this now that TimePoint is immutable?
        t = data.TimePoint(year="1984")
        # commenting out month_of_year here is enough to make the test pass
        t._month_of_year = None
        t._day_of_year = None
        t._week_of_year = None
        with self.assertRaises(RuntimeError):
            self.assertEqual("1984-01-01T00:00:00Z", str(t))
        # QUESTION: What was this test meant to do exactly?


if __name__ == '__main__':
    unittest.main()
