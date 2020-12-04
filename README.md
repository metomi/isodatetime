isodatetime
===========

[![Test](https://github.com/metomi/isodatetime/workflows/Test/badge.svg?event=push)](https://github.com/metomi/isodatetime/actions?query=workflow%3ATest)
[![codecov](https://codecov.io/gh/metomi/isodatetime/branch/master/graph/badge.svg)](https://codecov.io/gh/metomi/isodatetime)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.597555.svg)](https://doi.org/10.5281/zenodo.597555)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/1fd1147b75474d4d9a0f64bececf3bb5)](https://www.codacy.com/app/metomi/isodatetime?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=metomi/isodatetime&amp;utm_campaign=Badge_Grade)
[![PYPI Badge](https://img.shields.io/pypi/v/metomi-isodatetime)](https://pypi.org/project/metomi-isodatetime/)

Python [ISO8601 (2004)](https://www.iso.org/standard/40874.html)
full-specification parser and data model/manipulation utilities.
Intended to be used in a similar way to Python's datetime module.

## Installation

Install from PyPI:

```console
$ pip install metomi-isodatetime
```

Or build yourself:

```console
$ git clone https://github.com/metomi/isodatetime.git isodatetime
$ cd isodatetime
$ python setup.py install
```

## Usage

Python API:

<!-- GitHub Python syntax highlighting has issues with datetimes, Ruby works
     reasonably well as a stand-in. -->
```ruby
>>> import metomi.isodatetime.parsers as parse
>>> import metomi.isodatetime.dumpers as dump

# Dates and times
>>> date_time = parse.TimePointParser().parse('2000-01-01T00:00Z')
>>> date_time.month_of_year
1

# Durations
>>> duration = parse.DurationParser().parse('P1YT3H')
>>> duration.get_days_and_seconds()
(365.0, 10800.0)
>>> date_time + duration
<metomi.isodatetime.data.TimePoint: 2001-01-01T03:00:00Z>

# Recurrences
>>> recurrence = parse.TimeRecurrenceParser().parse('R/1999/P1Y')
>>> recurrence.get_next(date_time)
<metomi.isodatetime.data.TimePoint: 2001-01-01T00:00:00Z>

# Output
>>> dump.TimePointDumper().strftime(date_time, '%d/%M/%Y %H:%M:%S')
'01/00/2000 00:00:00'

```

CLI:

```console
$ isodatetime
2000-01-01T00:00:00Z
$ isodatetime 1066
1066
$ isodatetime 1066 --offset P1Y
1067
$ isodatetime R/2000/P1Y --max 3
2000-01-01T00:00:00Z
2001-01-01T00:00:00Z
2002-01-01T00:00:00Z
```

## Copyright and Terms of Use

Copyright (C) 2013-<span actions:bind='current-year'>2020</span> British Crown
(Met Office) & Contributors.

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU Lesser General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along
with this program.  If not, see [GNU licenses](http://www.gnu.org/licenses/).

## ISO 8601

[ISO 8601 (2004)](https://www.iso.org/standard/40874.html)
is an international standard for writing down date/time information.

It is the correct, internationally-friendly, computer-sortable way to
numerically represent date/time information.

Good reading material:
 * http://www.cl.cam.ac.uk/~mgk25/iso-time.html
 * http://www.tondering.dk/claus/calendar.html

Reference material:
 * http://www.iso.org/iso/home/standards/iso8601.htm
 * http://en.wikipedia.org/wiki/ISO_8601

### Dates and times

#### How do I write the year, month-of-year, and day-of-month down?

Syntax      | Example
 ---------- | ----------
 CCYYMMDD    | 20151231
 CCYY-MM-DD  | 2015-12-31

#### How about writing down the year, week-of-year, and day-of-week?

Syntax      | Example
 ---------- | ----------
 CCYYWwwD    | 2015W534
 CCYY-Www-D  | 2015-W53-4

#### How about writing down the year and day-of-year?

Syntax      | Example
 ---------- | ---------
 CCYYDDD     | 2015365
 CCYY-DDD    | 2015-365


#### How do I write just the year?
Either:
`CCYY`
or
`+XCCYY`

`+X` stands for a plus or minus sign (`+` or `-`), followed by a fixed,
agreed number of expanded year digits (`X`). For example, if we agree to have
2 expanded year digits, we can represent years from -999999 to +999999
(1000000 BC to 999999 AD). Note that 1 BC is the year 0 in the proleptic
Gregorian calendar used by ISO 8601.

For example, you can write the year 1995 AD as:
`1995`
or
`+001995` (using 2 expanded year digits).

Note: writing just the year where you mean a proper date implies Day 1 of
Month 1 in that year - `1995` implies `1995-01` => `1995-01-01` =>
`1995-01-01T00` => `1995-01-01T00:00` => `1995-01-01T00:00:00`.

#### How do I write just the year and month-of-year?
Either:
`CCYY-MM`
or
`+XCCYY-MM` (+ standing in here for a `+` or `-` sign)

(not allowed: `CCYYMM` or `+XCCYYMM`).

#### How do I write dates past the year 9999 and before 0000?

Syntax        | Example (2 expanded year digits)
 ------------ | ---------
 +XCCYYMMDD   | +0020151231
 +XCCYY-MM-DD | +002015-12-31
 +XCCYYWwwD   | +002015W534
 +XCCYY-Www-D | +002015-W53-4
 +XCCYYDDD    | +002015365
 +XCCYY-DDD   | +002015-365

#### How do I write down time information by itself?

Syntax             | Example
 ----------------- | -------
 hhmmss             | 083000
 hhmm               | 0830
 hh:mm:ss           | 17:45:01
 hh:mm              | 17:45
 hh                 | 08

#### How do I write down time information at a date in ISO 8601?

Write the time after the date, separated with a `T`:

Syntax              | Example
 ------------------ | -------------------
 CCYYMMDDThhmmss     | 20151231T063101
 CCYY-MM-DDThh:mm:ss | 2015-12-31T06:31:01
 CCYYWwwDThhmmss     | 2015W534T063101
 CCYY-Www-DThh:mm:ss | 2015-W53-4T06:31:01
 CCYYDDDThhmmss      | 2015365T063101
 CCYY-DDDThh:mm:ss   | 2015-365T06:31:01

#### What about just the hour and minute at a date?

Syntax           | Example
 --------------- | ----------------
 CCYYWwwDThhmm    | 2015W534T0631
 CCYY-Www-DThh:mm | 2015-W53-4T06:31

#### What about just the hour at a date?

Syntax           | Example
 --------------- | -------------
 CCYYMMDDThh      | 20151231T06
 CCYY-MM-DDThh    | 2015-12-31T06

#### What about decimal parts of the hour or minute or second?

Use a comma or period to delimit the decimal part, and don't include any
smaller units:

Syntax             | Example
 ----------------- | ------------------
 CCYYMMDDThh,ii     | 20151231T06,5
 CCYYMMDDThh.ii     | 20151231T06.5
 CCYYMMDDThhmm,nn   | 20151231T0631,3333
 CCYYMMDDThhmm.nn   | 20151231T0631.3333
 CCYYMMDDThhmmss,tt | 20151231T063101,25671
 CCYYMMDDThhmmss.tt | 20151231T063101.25671


#### How do I specify a time zone?

If the time zone is UTC, use "Z" - otherwise, use a numeric representation
of the hours and minutes difference from UTC.

Note that this difference is (TIMEZONE - UTC) - so longitudes east of 0 tend
to have positive differences, and west of 0 usually have negative differences.

Syntax                     | Example
 ------------------------- | -------------------------
 CCYYMMDDThhmmssZ           | 20151231T063101Z
 CCYY-MM-DDThh:mm:ssZ       | 2015-12-31T06:31:01Z
 CCYYMMDDThhmmss-hh         | 20151231T013101-05
 CCYY-MM-DDThh:mm:ss-hh     | 2015-12-31T01:31:01-05
 CCYYMMDDThhmmss+hh         | 20151231T083101+02
 CCYY-MM-DDThh:mm:ss+hh     | 2015-12-31T08:31:01+02
 CCYYMMDDThhmmss-hhmm       | 20151230T203101-1000
 CCYY-MM-DDThh:mm:ss-hh:mm  | 2015-12-30T20:31:01-10:00
 CCYYMMDDThhmmss+hhmm       | 20151231T193101+1300
 CCYY-MM-DDThh:mm:ss+hh:mm  | 2015-12-31T19:31:01+13:00


### Durations

#### How do I write down a certain period of time in X units?

A "P" followed by the number of units (optionally including a decimal part)
followed by a designator to mark the units:

Unit type | Unit designator
 -------- | ---------------
 years    | Y
 months   | M
 weeks    | W
 days     | D
 hours    | H
 minutes  | M
 seconds  | S

If the unit is one of hours, minutes, or seconds, you need a leading "T"
to delimit time from date:

Syntax    | Example  | Meaning
 -------- | -------- | ------------------------
 PnY      |  P2Y     | 2 years
 PTnM     |  PT7M    | 7 minutes (note the 'T')
 PnM      |  P10M    | 10 months
 PnDTnH   |  P5DT6H  | 5 days and 6 hours
 PTn,oH   |  PT5,5H  | 5 and a half hours
 PTn.oH   |  PT5.5H  | 5 and a half hours
 PnW      |  P2W     | 2 weeks

Combining any other unit with weeks is not allowed. Decimals may only be used
for hours, minutes and seconds.

Note that years and months are "nominal" durations, whose exact length of time
depends on their position in the calendar. E.g., a duration of 1 calendar year
starts on a particular day of a particular month and ends on the same day of
the same month in the following calendar year, and may be different to 365 days
in the Gregorian calendar due to leap years.

Conversely, weeks, days, hours, minutes and seconds are exact units, so
`P1W == P7D`, `P1D == PT24H` and `PT1H == PT60M` etc. are always true.
(Although ISO 8601 specifies that weeks and days are nominal durations, there
is no case where they are not exact in our implementation.)
<!-- ...because TimePoints always have time zones assigned to them (apart
from truncated TimePoints, but you can't add Durations to truncated
TimePoints). Local time zones don't actually exist in our implementation. -->

A supplementary format (which has to be agreed in advance) is to specify a
date-time-like duration (`PCCYY-MM-DDThh:mm:ss`) where the numbers given for
years, months, days, hours, minutes, and seconds are used literally
(`P1995-00-00T00:10:00` = `P1995YT10M`).

### Recurring date-time series

#### 1. Recur with a duration given by the difference between a start date and a subsequent date

Example Syntax                 | Example                          | Meaning
 ----------------------------- | -------------------------------- | ------------------------------------------------------------------
R/CCYY/CCYY                    | R/2010/2014                      | Repeat every 4 years, starting at 2010-01-01
R/CCYY-MM/CCYY-DDD             | R/2010-01/2012-045               | Repeat every 2 years and 44 days, starting at 2010-01-01
Rn/CCYY-Www-D/CCYY-Www-D       | R5/2015-W05-2/2015-W07-3         | Repeat every 2 weeks and 1 day, five times, starting at 2015-W05-2
Rn/CCYY-MM-DDThh/CCYY-MM-DDThh | R1/1925-02-11T00Z/2027-06-01T00Z | Repeat once at 1925-02-11T00Z (note the end date-time is ignored)

#### 2. Recur with a specified duration, starting at a context date-time

(You have to supply the context somewhere else)

Example Syntax        | Example          | Meaning
 -------------------- | ---------------- | ------------------------------------------------------------------------------
R/PnMnDTnM            | R/P10M3DT45M     | Repeat every 10 months, 3 days, and 45 minutes from a context start date-time.
Rn/PnY                | R2/P4Y           | Repeat every 4 years, for a total of 2 times, from a context start date-time.

#### 3. Recur with a specified duration starting at a particular date-time

Example Syntax             | Example                  | Meaning
 ------------------------- | ------------------------ | ----------------------------------------------------------------------------------------------
R/CCYYMMDDThhZ/PTnH        | R/20201231T00Z/PT12H     | Repeat every 12 hours starting at 2020-12-31T00Z
R/CCYY-Www-D/PnW           | R/2012-W02-1/P1W         | Repeat weekly starting at Monday in the second ISO week of 2012
R/CCYYDDDThhmm/PnD         | R/1996291T0630+0100/P2D  | Repeat every 2 days starting on the 291st day of 1996 at 06:30, UTC + 1
Rn/CCYY-MM-DDThh:mm/PTnH   | R2/19900201T06Z/PT12H    | Repeat every 12 hours, for a total of 2 repetitions, starting at 1990-02-01T06Z
Rn/CCYY-Www-D/PnW          | R5/2012-W02-1/P1W        | Repeat weekly, for a total of 5 repetitions, starting at Monday in the second ISO week of 2012
Rn/CCYYDDDThhmm/PnD        | R1/1996291T0630Z/P2D     | Repeat once on the 291st day of 1996 at 06:30 (note the duration is ignored)

#### 4. Recur with a specified duration ending at a particular date-time

The starting date-time of the recurrence is calculated from the specified
duration.

Example Syntax             | Example                  | Meaning
 ------------------------- | ------------------------ | ---------------------------------------------------------------
R/PTnH/CCYY-MM-DDThhZ      | R/PT1H/2012-01-02T00Z    | Repeat hourly, ending at 2012-01-02T00Z (therefore repeats on the hour)
R/PnY/CCYY                 | R/P3Y/2000               | Repeat every 3 years, ending at 2000-01-01 (therefore repeats at 00:00 January 1st)
R/PTnS/+XCCYYDDDThhmm      | R/PT5s/-002500012T1800   | Repeat every 5 seconds, ending on the 12th day in 2501 BC at 18:00 (using 2 expanded year digits)
Rn/PnYTnM/CCYY-MM-DDThhZ   | R5/P1YT5M/2012-01-02T00Z | Repeat every year and 5 minutes, five times, ending at 2012-01-02T00Z
Rn/PnM/CCYY-MM             | R4/P1M/2000-05           | Repeat monthly, four times, ending at 2000-05-01 (therefore repeats on the first of the month)
