# isodatetime changes

Go to https://github.com/metomi/isodatetime/milestones?state=closed
for a full listing of issues for each release.

--------------------------------------------------------------------------------

## Next Release (2014-Q3?)

This will be the 5th release of isodatetime.

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
