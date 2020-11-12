# isodatetime changes

Go to https://github.com/metomi/isodatetime/milestones?state=closed
for a full listing of issues for each release.

<!-- The topmost release date is automatically updated by GitHub Actions. When
creating a new release entry be sure to copy & paste the span tag with the
`actions:bind` attribute, which is used by a regex to find the text to be
updated. Only the first match gets replaced, so it's fine to leave the old
ones in. -->

--------------------------------------------------------------------------------

## isodatetime 2.1.0 (<span actions:bind='release-date'>Upcoming, 2020</span>)

This is the 15th release of isodatetime. Requires Python 3.5+.

### Noteworthy Changes

[#165](https://github.com/metomi/isodatetime/pull/165):
Data classes are now immutable and hashable.

[#183](https://github.com/metomi/isodatetime/pull/183):
**Fixed a longstanding mistake in the implementation of TimeRecurrence format
number 1.** Also implemented support for adding/subtracting Duration instances
to/from TimeRecurrence instances.

[#187](https://github.com/metomi/isodatetime/pull/187):
Replaced `TimePoint.get("attribute_name")` method with individual attributes
`TimePoint.attribute_name`. Fixed a bug in rounding decimal properties of
TimePoints.

--------------------------------------------------------------------------------

## isodatetime 2.0.2 (Released 2020-07-01)

This is the 14th release of isodatetime. Requires Python 3.5+.

### Noteworthy Changes

[#148](https://github.com/metomi/isodatetime/pull/148):
Exceptions have moved to `metomi.isodatetime.exceptions`.

[#151](https://github.com/metomi/isodatetime/pull/151):
CLI can now read in from piped stdin.

[#157](https://github.com/metomi/isodatetime/pull/157):
TimePoints can no longer be created with out-of-bounds values, e.g.
`2020-00-00`, `2020-13-32T25:60`, `--02-30` are not valid.

--------------------------------------------------------------------------------

## isodatetime 2.0.1 (Released 2019-07-23)

This is the 13th release of isodatetime.

This release requires Python 3.5 or above.

Note the major change in namespace from `isodatetime` to `metomi.isodatetime`.

### Noteworthy Changes

[#122](https://github.com/metomi/isodatetime/pull/122):
CLI take mixed required and optional arguments (Python 3.7+ only).

[#127](https://github.com/metomi/isodatetime/pull/127):
Raise a useful `ValueError` if time point is invalid.

[#130](https://github.com/metomi/isodatetime/pull/130):
Support the CF compatible calendar mode strings `360_day`, `365_day` & `366_day`

[#132](https://github.com/metomi/isodatetime/pull/132):
Change namespace of `isodatetime` to `metomi.isodatetime`

--------------------------------------------------------------------------------

## isodatetime 2.0.0 (Released 2019-01-22)

This is the 12th release of isodatetime.

This release requires Python 3.4 or above.

Note the move of the version string to a semantic scheme to avoid issues with
packaging utilities.

### Highlights

[#111](https://github.com/metomi/isodatetime/pull/111):
Python 3.4+ only. Drop support for Python 2.

[#117](https://github.com/metomi/isodatetime/pull/117):
Improved installation instruction and usage examples.

[#114](https://github.com/metomi/isodatetime/pull/114):
Added `isodatetime` command line interface.

### Noteworthy Changes

[#112](https://github.com/metomi/isodatetime/pull/112):
Support RPM build.

[#119](https://github.com/metomi/isodatetime/pull/119):
Fixed time point dumper time zone inconsistency.

[#118](https://github.com/metomi/isodatetime/pull/118):
Fixed time point dumper date type inconsistency.

--------------------------------------------------------------------------------

## isodatetime 2018.11.0 (Released 2018-11-05)

This is the 11th release of isodatetime.

This release features general improvement to unit test coverage, amongst
various fixes.

### Noteworthy Changes

[#106](https://github.com/metomi/isodatetime/pull/106),
[#108](https://github.com/metomi/isodatetime/pull/108):
Fix ordinal date and week addition.

[#103](https://github.com/metomi/isodatetime/pull/103):
Fix `TimePoint` dumper behaviour after the `TimePoint` object has been copied.

[#93](https://github.com/metomi/isodatetime/pull/93):
Fix for timezone offsets where minutes are not 0.

[#87](https://github.com/metomi/isodatetime/pull/87):
Add `setup.py`.

--------------------------------------------------------------------------------

## isodatetime 2018.09.0 (Released 2018-09-11)

This is the 10th release of isodatetime.

### Noteworthy Changes

[#86](https://github.com/metomi/isodatetime/pull/86):
New TimePoint method to find the next smallest property that is missing from a
truncated representation.

--------------------------------------------------------------------------------

## isodatetime 2018.02.0 (Released 2018-02-06)

This is the 9th release of isodatetime.

### Noteworthy Changes

[#82](https://github.com/metomi/isodatetime/pull/82):
Fix subtracting a later timepoint from an earlier one.

--------------------------------------------------------------------------------

## isodatetime 2017.08.0 (Released 2017-08-09)

This is the 8th release of isodatetime.

### Noteworthy Changes

[#75](https://github.com/metomi/isodatetime/pull/75):
Fix error string for bad conversion for strftime/strptime.

[#74](https://github.com/metomi/isodatetime/pull/74):
Slotted the data classes to improve memory footprint.

--------------------------------------------------------------------------------

## isodatetime 2017.02.1 (Released 2017-02-21)

This is the 7th release of isodatetime. Admin only release.

--------------------------------------------------------------------------------

## isodatetime 2017.02.0 (Released 2017-02-20)

This is the 6th release of isodatetime.

### Noteworthy Changes

[#73](https://github.com/metomi/isodatetime/pull/73):
Fix adding duration not in weeks and duration in weeks.

--------------------------------------------------------------------------------

## isodatetime 2014.10.0 (Released 2014-10-01)

This is the 5th release of isodatetime.

### Noteworthy Changes

[#63](https://github.com/metomi/isodatetime/pull/63):
Remove unnecessary unicode, which happened to trigger a Python 2.6.2 unicode
bug.

[#61](https://github.com/metomi/isodatetime/pull/61):
Fix `date1 - date2` where `date2` is greater than `date1` and `date1` and
`date2` are in different calendar years.

[#60](https://github.com/metomi/isodatetime/pull/60):
Stricter dumper year bounds checking.

--------------------------------------------------------------------------------

## isodatetime 2014.08.0 (Released 2014-08-11)

This is the 4th release of isodatetime.

### Noteworthy Changes

[#59](https://github.com/metomi/isodatetime/pull/59):
Rename *time interval* and *interval* to *duration*.

[#58](https://github.com/metomi/isodatetime/pull/58):
Raise error when a year cannot be represented with the given number of year
digits.

[#57](https://github.com/metomi/isodatetime/pull/57):
Speeds up calculations involving counting the days over a number of consecutive
years.

--------------------------------------------------------------------------------

## isodatetime 2014.07.0 (Released 2014-07-29)

This is the 3rd release of isodatetime.

### Noteworthy Changes

[#56](https://github.com/metomi/isodatetime/pull/56):
Replace the Unicode plus/minus sign with a single plus sign to force
a sign in formatting.

[#52](https://github.com/metomi/isodatetime/pull/52):
More flexible API for calendar mode.

[#48](https://github.com/metomi/isodatetime/pull/48):
`TimeInterval` class: add `get_seconds` method and input prettifying.

--------------------------------------------------------------------------------

## isodatetime 2014.06.0 (Released 2014-06-19)

This is the 2nd release of isodatetime. Enjoy!

### Noteworthy Changes

[#40](https://github.com/metomi/isodatetime/pull/40):
Support 360 day calendar.

[#35](https://github.com/metomi/isodatetime/pull/35),
[#43](https://github.com/metomi/isodatetime/pull/43):
Implement (and fix) local timezone for `TimePoint`.

[#29](https://github.com/metomi/isodatetime/pull/29),
[#30](https://github.com/metomi/isodatetime/pull/30),
[#32](https://github.com/metomi/isodatetime/pull/32),
[#36](https://github.com/metomi/isodatetime/pull/36),
[#42](https://github.com/metomi/isodatetime/pull/42),
[#44](https://github.com/metomi/isodatetime/pull/44):
Implement subset of strftime/strptime POSIX standard.

[#28](https://github.com/metomi/isodatetime/pull/28):
Fix get next point for single-repetition recurrences.

--------------------------------------------------------------------------------

## isodatetime 2014-03 (Released 2014-03-13)

This is the 1st release of isodatetime. Enjoy!
