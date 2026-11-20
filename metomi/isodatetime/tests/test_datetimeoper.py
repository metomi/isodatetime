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
"""Test isodatetime.datetimeoper functionalities."""


import os
from unittest.mock import patch

import pytest

from metomi.isodatetime.data import (
    get_timepoint_from_seconds_since_unix_epoch as seconds2point,
)
import metomi.isodatetime.datetimeoper as idt_dtoper
from metomi.isodatetime.exceptions import OffsetValueError


@patch('metomi.isodatetime.datetimeoper.now2point')
def test_process_time_point_str_now_0(mock_now_func):
    """DateTimeOperator.process_time_point_str()"""
    # 2009-02-13T23:31:30Z
    mock_now = seconds2point(1234567890)
    mock_now_func.return_value = mock_now
    datetimeoper = idt_dtoper.DateTimeOperator()
    assert str(mock_now) == datetimeoper.process_time_point_str()
    assert str(mock_now) == datetimeoper.process_time_point_str(
        datetimeoper.STR_NOW
    )


@patch('metomi.isodatetime.datetimeoper.now2point')
def test_process_time_point_str_ref_0(mock_now_func):
    """DateTimeOperator.process_time_point_str('ref')

    But without explicit reference time, so default to now.
    """
    # 2009-02-13T23:31:30Z
    mock_now = seconds2point(1234567890)
    mock_now_func.return_value = mock_now
    datetimeoper = idt_dtoper.DateTimeOperator()
    # Ensure that the ISODATETIMEREF environment variable is not set
    # Or the test may not work.
    environ = os.environ.copy()
    if datetimeoper.ENV_REF in environ:
        del environ[datetimeoper.ENV_REF]
    with patch.dict(os.environ, environ, clear=True):
        assert str(mock_now) == datetimeoper.process_time_point_str(
            datetimeoper.STR_REF
        )


def test_process_time_point_str_ref_1():
    """DateTimeOperator.process_time_point_str('ref')

    With explicit reference time.
    """
    # 2009-02-13T23:31:30Z
    ref_point_str = str(seconds2point(1234567890))
    datetimeoper = idt_dtoper.DateTimeOperator(
        ref_point_str=ref_point_str)
    assert ref_point_str == datetimeoper.process_time_point_str(
        datetimeoper.STR_REF
    )


def test_process_time_point_str_ref_2():
    """DateTimeOperator.process_time_point_str('ref')

    With explicit reference time as ISODATETIMEREF environment variable.
    """
    # 2009-02-13T23:31:30Z
    ref_point_str = str(seconds2point(1234567890))
    # Set ISODATETIMEREF.
    # Or the test may not work.
    environ = os.environ.copy()
    environ[idt_dtoper.DateTimeOperator.ENV_REF] = (
        ref_point_str)
    with patch.dict(os.environ, environ):
        datetimeoper = idt_dtoper.DateTimeOperator()
        assert ref_point_str == datetimeoper.process_time_point_str(
            datetimeoper.STR_REF
        )


@pytest.mark.parametrize(
    'point_str, offsets, print_format, expected', [
        pytest.param(
            'Fri 11 Jan 10:40:15 UTC 2019',
            None,
            idt_dtoper.DateTimeOperator.CURRENT_TIME_DUMP_FORMAT_Z,
            '2019-01-11T10:40:15Z',
            id='unix-time',
        ),
        pytest.param(
            '2009-02-13T23:31:30Z', None, None,
            '2009-02-13T23:31:30Z',
            id='basic',
        ),
        pytest.param(
            '2009-02-13T23:31:30Z', ['PT1H'], None,
            '2009-02-14T00:31:30Z',
            id='positive-offset',
        ),
        pytest.param(
            '2009-02-13T23:31:30Z', ['P0000-00-00T01'], None,
            '2009-02-14T00:31:30Z',
            id='duration-offset',
        ),
        pytest.param(
            '2009-02-13T23:31:30Z', ['-P1D'], None,
            '2009-02-12T23:31:30Z',
            id='negative-offset',
        ),
        pytest.param(
            '2009-02-13T23:31:30Z', ['PT1H', '-PT60M'], None,
            '2009-02-13T23:31:30Z',
            id='offsets-cancel-out',
        ),
        pytest.param(
            '2009-02-13T23:31:30Z', ['-P1DT1H'], None,
            '2009-02-12T22:31:30Z',
            id='combined-offset',
        ),
        pytest.param(
            '2009-02-13T23:31:30Z', ['-P1D', '-PT1H'], None,
            '2009-02-12T22:31:30Z',
            id='multiple-offsets',
        ),
    ])
def test_process_time_point_str_x(
    point_str, offsets, print_format, expected
):
    """DateTimeOperator.process_time_point_str(...)

    Basic parse and dump of a time point string.
    """
    d = idt_dtoper.DateTimeOperator()
    assert (
        d.process_time_point_str(point_str, offsets, print_format) == expected
    )


@pytest.mark.parametrize(
    'point_str, offsets, exception, message', [
        pytest.param(
            'teatime', None, ValueError, None,
            id='bad-time-point',
        ),
        pytest.param(
            '2009-02-13T23:31:30Z', ['ages'], OffsetValueError,
            'ages: bad offset value',
            id='bad-offset',
        ),
        pytest.param(
            '2009-02-13T23:31:30Z', ['P0000-W01-1'], OffsetValueError,
            'P0000-W01-1: bad offset value',
            id='unsupported-duration-offset',
        ),
    ])
def test_process_time_point_str_x_bad(point_str, offsets, exception, message):
    datetimeoper = idt_dtoper.DateTimeOperator()
    with pytest.raises(exception) as ctxmgr:
        datetimeoper.process_time_point_str(point_str, offsets)
    if message is not None:
        assert str(ctxmgr.value) == message


@pytest.mark.parametrize(
    'cal,str_in,offsets,str_out', [
        # 360day
        ('360day', '20130301', ['-P1D'], '20130230'),
        ('360day', '20130230', ['P1D'], '20130301'),
        # 360_day
        ('360_day', '20130301', ['-P1D'], '20130230'),
        ('360_day', '20130230', ['P1D'], '20130301'),
        # 365day
        ('365day', '20130301', ['-P1D'], '20130228'),
        ('365day', '20130228', ['P1D'], '20130301'),
        # 365_day
        ('365_day', '20130301', ['-P1D'], '20130228'),
        ('365_day', '20130228', ['P1D'], '20130301'),
        # 366day
        ('366day', '20130301', ['-P1D'], '20130229'),
        ('366day', '20130229', ['P1D'], '20130301'),
        # 366_day
        ('366_day', '20130301', ['-P1D'], '20130229'),
        ('366_day', '20130229', ['P1D'], '20130301'),
    ])
def test_process_time_point_str_calendar(cal, str_in, offsets, str_out):
    """DateTimeOperator.process_time_point_str(...)

    Alternate calendars.
    """
    assert idt_dtoper.DateTimeOperator.get_calendar_mode() == 'gregorian'
    with pytest.raises(KeyError):
        idt_dtoper.DateTimeOperator.set_calendar_mode('milkywaygalactic')
    # Calendar mode, is unfortunately, a global variable,
    # so needs to reset value on return.
    calendar_mode = idt_dtoper.DateTimeOperator.get_calendar_mode()
    # Calendar mode by constructor.
    try:
        datetimeoper = idt_dtoper.DateTimeOperator(calendar_mode=cal)
        assert str_out == datetimeoper.process_time_point_str(str_in, offsets)
    finally:
        idt_dtoper.DateTimeOperator.set_calendar_mode(calendar_mode)
    # Calendar mode by environment variable
    try:
        environ = os.environ.copy()
        key = idt_dtoper.DateTimeOperator.ENV_CALENDAR_MODE
        environ[key] = cal
        with patch.dict(os.environ, environ, clear=True):
            datetimeoper = idt_dtoper.DateTimeOperator()
            assert str_out == datetimeoper.process_time_point_str(
                str_in, offsets)
    finally:
        idt_dtoper.DateTimeOperator.set_calendar_mode(calendar_mode)


@pytest.mark.parametrize(
    'parse_format,print_format,point_str_in,point_str_out', [
        ('%d/%m/%Y %H:%M:%S', '%Y-%m-%dT%H:%M:%S',
         '24/12/2012 06:00:00', '2012-12-24T06:00:00'),
        ('%Y,%M,%d,%H', '%Y%M%d%H', '2014,01,02,05', '2014010205'),
        ('%Y%m%d', '%y%m%d', '20141231', '141231'),
        ('%Y%m%d%H%M%S', '%s', '20140402100000', '1396432800'),
        ('%s', '%Y%m%dT%H%M%S%z', '1396429200', '20140402T090000+0000'),
        ('%d/%m/%Y %H:%M:%S', 'CCYY-MM-DDThh:mm',
         '24/12/2012 06:00:00', '2012-12-24T06:00'),
        (None, 'CCYY-MM-DDThh:mm+01:00',
         '2014-091T15:14:03Z', '2014-04-01T16:14+01:00'),
        (None, '%m', '2014-02-01T04:05:06', '02'),
        (None, '%Y', '2014-02-01T04:05:06', '2014'),
        (None, '%H', '2014-02-01T04:05:06', '04'),
        (None, '%Y%m%d_%H%M%S', '2014-02-01T04:05:06', '20140201_040506'),
        (None, '%Y.file', '2014-02-01T04:05:06', '2014.file'),
        (None, 'y%Ym%md%d', '2014-02-01T04:05:06', 'y2014m02d01'),
        (None, '%F', '2014-02-01T04:05:06', '2014-02-01'),
    ])
def test_process_time_point_str_format(
    parse_format, print_format, point_str_in, point_str_out
):
    """DateTimeOperator.process_time_point_str(...)

    With parse_format and print_format.
    """
    datetimeoper = idt_dtoper.DateTimeOperator(
        utc_mode=True,
        parse_format=parse_format)
    assert point_str_out == datetimeoper.process_time_point_str(
        point_str_in, print_format=print_format)


def test_process_time_point_str_format_bad_parse_format():
    datetimeoper = idt_dtoper.DateTimeOperator(parse_format='%o')
    with pytest.raises(ValueError) as ctxmgr:
        datetimeoper.process_time_point_str('0000')
    assert str(ctxmgr.value) == "'o' is a bad directive in format '%o'"


@pytest.mark.parametrize('print_format,duration_str_in,duration_out', [
    ('s', 'PT1M', 60.0),
    ('s', 'P1DT1H1M1S', 90061.0),
    ('m', 'PT1S', 0.0166666666667),
    ('h', 'P832DT23H12M45S', 19991.2125),
    ('S', '-PT1M1S', -61.0),
])
def test_format_duration_str_x(print_format, duration_str_in, duration_out):
    """DateTimeOperator.format_duration_str(...)"""
    datetimeoper = idt_dtoper.DateTimeOperator()
    assert datetimeoper.format_duration_str(
        duration_str_in, print_format
    ) == pytest.approx(duration_out)


@pytest.mark.parametrize('print_format,duration_str_in', [
    ('y', 'PT1M'),
    ('s', 'quickquick'),
])
def test_format_duration_str_bad(print_format, duration_str_in):
    datetimeoper = idt_dtoper.DateTimeOperator()
    with pytest.raises(ValueError):
        datetimeoper.format_duration_str(duration_str_in, print_format)


@pytest.mark.parametrize(
    'time_point_str1,time_point_str2,offsets1,offsets2,print_format,'
    'duration_print_format,expected', [
        pytest.param(
            '20130101T12',
            '20130301',
            None,
            None,
            None,
            None,
            'P58DT12H',
            id='positive',
        ),
        pytest.param(
            '2026',
            '20260101T0450',
            None,
            None,
            None,
            None,
            'PT4H50M',
            id='positive-2',
        ),
        pytest.param(
            '2026-11-01',
            'Mon Nov  2 06:30:00 2026',
            None,
            None,
            None,
            None,
            'P1DT6H30M',
            id='ctime',
        ),
        pytest.param(
            '2026-11-01',
            'Mon 2 Nov 06:30:00 UTC 2026',
            None,
            None,
            None,
            None,
            'P1DT6H30M',
            id='unix-date',
        ),
        pytest.param(
            # Use (3.1 - 3.0) to bypass str(float) precision issue
            '20190101T010203',
            '20190101T010203.1',
            None,
            None,
            None,
            None,
            'PT%sS' % (str(3.1 - 3.0).replace('.', ',')),
            id='fractional-duration',
        ),
        pytest.param(
            # Use (3.1 - 3.0) to bypass str(float) precision issue
            '20190101T010203',
            '20190101T010203.1',
            None,
            None,
            's',
            None,
            str(3.1 - 3.0),
            id='fractional-seconds',
        ),
        pytest.param(
            '20140101',
            'ref',
            ['P11M24D'],
            None,
            None,
            None,
            'P12D',
            id='reference-offset',
        ),
        pytest.param(
            '20100101T00',
            '20100201T00',
            None,
            ['P1D'],
            None,
            None,
            'P32D',
            id='second-offset',
        ),
        pytest.param(
            '20151225T00',
            '20151225',
            None,
            None,
            None,
            None,
            'P0Y',
            id='neutral',
        ),
        pytest.param(
            '20150101T12',
            '20130301',
            None,
            None,
            None,
            None,
            '-P671DT12H',
            id='negative',
        ),
        pytest.param(
            '20130101T12',
            '20130301',
            None,
            None,
            'y,m,d,h,M,s',
            None,
            '0,0,58,12,0,0',
            id='alternate-format',
        ),
        pytest.param(
            '0000',
            '0000',
            ['-PT2M'],
            None,
            'y,m,d,h,M,s',
            None,
            '0,0,0,0,2,0',
            id='alternate-offset',
        ),
        pytest.param(
            '2000-01-01T00:00:00',
            '2000-01-01T01:00:00',
            None,
            None,
            None,
            's',
            3600.0,
            id='seconds-positive',
        ),
        pytest.param(
            '2000-01-01T00:00:00',
            '2000-01-01T00:00:00',
            None,
            None,
            None,
            's',
            0.0,
            id='seconds-neutral',
        ),
        pytest.param(
            '2000-01-01T00:00:00',
            '1999-12-31T23:00:00',
            None,
            None,
            None,
            's',
            -3600.0,
            id='seconds-negative',
        ),
    ])
def test_diff_time_point_strs(
    time_point_str1,
    time_point_str2,
    offsets1,
    offsets2,
    print_format,
    duration_print_format,
    expected,
    mock_local_time_zone,
):
    """DateTimeOperator.diff_time_point_strs(...)"""
    mock_local_time_zone(0)
    datetimeoper = idt_dtoper.DateTimeOperator(ref_point_str='20150106')
    assert (
        datetimeoper.diff_time_point_strs(
            time_point_str1,
            time_point_str2,
            offsets1,
            offsets2,
            print_format,
            duration_print_format,
        )
        == expected
    )
