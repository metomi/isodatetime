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

"""This tests the timezone module."""

from typing import Callable, Tuple
import pytest

from metomi.isodatetime import timezone


@pytest.mark.parametrize('dst', [True, False])
@pytest.mark.parametrize(
    'tz_seconds, expected_no_dst, tz_dst_seconds, expected_with_dst',
    [
        pytest.param(
            45900, (12, 45),
            49500, (13, 45),
            id="pacific/chatham, +12:45 and +13:45"
        ),
        pytest.param(
            20700, (5, 45),
            20700, (5, 45),
            id="asia/kathmandu, +05:45"
        ),
        pytest.param(
            3600, (1, 0),
            7200, (2, 0),
            id="europe/oslo, +01:00 and +02:00"
        ),
        pytest.param(
            0, (0, 0),
            0, (0, 0),
            id="UTC"
        ),
        pytest.param(
            0, (0, 0),
            3600, (1, 0),
            id="europe/london, +00:00 and +01:00"
        ),
        pytest.param(
            -12600, (-3, -30),
            -9000, (-2, -30),
            id="america/st_johns, -03:30 and -02:30"
        ),
        pytest.param(
            -5*3600, (-5, 0),
            -4*3600, (-4, 0),
            id="america/new_york, -05:00 and -04:00,"
        ),
        pytest.param(
            -8100, (-2, -15),
            -8100, (-2, -15),
            id="hypothetical -02:15"
        ),
        pytest.param(
            -1800, (0, -30),
            -2400, (0, -40),
            id="hypothetical -0:30 and -0:40"
        ),
    ]
)
def test_get_local_time_zone(
    dst: bool,
    tz_seconds: int,
    expected_no_dst: Tuple[int, int],
    tz_dst_seconds: int,
    expected_with_dst: Tuple[int, int],
    mock_local_time_zone: Callable
):
    """Test that the hour/minute returned is correct.

    Params:
        dst: Whether to simulate daylight savings time.
        tz_seconds: Time zone UTC offset when not in DST.
        expected_no_dst: Expected return value when in DST.
        tz_dst_seconds: Time zone UTC offset when in DST.
        expected_with_dst: Expected return value when not in DST.
    """
    mock_local_time_zone(
        tz_seconds,
        tz_dst_seconds if dst else 0
    )
    expected = expected_with_dst if dst else expected_no_dst
    assert timezone.get_local_time_zone() == expected


@pytest.mark.parametrize(
    'tz_seconds, expected_formats',
    [
        pytest.param(
            0, ('Z', 'Z', 'Z'),  # flags are never used for UTC
            id="UTC"
        ),
        # Positive values, some with minutes != 0
        pytest.param(
            28800, ('+0800', '+08:00', '+08'),
            id="asia/macao"
        ),
        pytest.param(
            45900, ('+1245', '+12:45', '+1245'),
            id="pacific/chatham"
        ),
        # Negative values, some with minutes != 0
        pytest.param(
            -3*3600, ('-0300', '-03:00', '-03'),
            id="america/buenos_aires"
        ),
        pytest.param(
            -12600, ('-0330', '-03:30', '-0330'),
            id="america/st_johns"
        ),
        pytest.param(
            -8100, ('-0215', '-02:15', '-0215'),
            id="hypothetical -02:15"
        ),
        pytest.param(
            -1800, ('-0030', '-00:30', '-0030'),
            id="hypothetical -00:30"
        ),
    ]
)
def test_get_local_time_zone_format(
    tz_seconds: int,
    expected_formats: Tuple[int, int, int],
    mock_local_time_zone: Callable
):
    """Test that the UTC offset string format is correct.

    Params:
        tz_seconds: The time zone's UTC offset.
        expected_formats: The expected return values for normal, extended
            and reduced formats, respectively.
    """
    # DST is not really important for this test
    mock_local_time_zone(tz_seconds)
    for i, tz_format_mode in enumerate([
        timezone.TimeZoneFormatMode.normal,
        timezone.TimeZoneFormatMode.extended,
        timezone.TimeZoneFormatMode.reduced
    ]):
        expected = expected_formats[i]
        assert timezone.get_local_time_zone_format(tz_format_mode) == expected
