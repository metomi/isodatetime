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

import pytest
import time
from unittest.mock import Mock


@pytest.fixture
def mock_local_time_zone(monkeypatch: pytest.MonkeyPatch):
    """A pytest fixture that simulates a given local system time zone.

    Args:
        seconds: The number of seconds UTC offset for the base time zone.
        dst_seconds: The number of seconds UTC offset for the daylight savings
            time zone.

    Note: these args are positive for time zones East of the prime meridian
    and negative for West.
    """
    def _mock_local_time_zone(seconds: int, dst_seconds: int = 0) -> None:
        is_dst = 1 if dst_seconds else 0
        mock_time = Mock(spec=time)
        mock_time.timezone = -seconds
        mock_time.altzone = -dst_seconds
        mock_time.daylight = is_dst
        mock_time.localtime.return_value = Mock(tm_isdst=is_dst)
        monkeypatch.setattr('metomi.isodatetime.timezone.time', mock_time)
    return _mock_local_time_zone
