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

import os
from setuptools import setup
# Monkey patching to disable version normalization, as we are using dates with
# leading zeroes
# https://github.com/pypa/setuptools/issues/308
from setuptools.extern.packaging import version
from isodatetime import __version__


version.Version = version.LegacyVersion


def read(fname):
    """Utility function to read the README file.

    Used for the long_description. It's nice, because now 1) we have a top
    level README file and 2) it's easier to type in the README file than to
    put a raw string in below ..."""
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="isodatetime",
    version=__version__,
    author="Met Office",
    author_email="metomi@metoffice.gov.uk",
    description=("Python ISO 8601 date time parser" +
                 " and data model/manipulation utilities"),
    license="LGPLv3",
    keywords="isodatetime datetime iso8601 date time parser",
    url="https://github.com/metomi/isodatetime",
    packages=['isodatetime'],
    long_description=read('README.md'),
    platforms='any',
    install_requires=[],
    python_requires='>=2.6, <3.0',
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        ("License :: OSI Approved" +
         " :: GNU Lesser General Public License v3 (LGPLv3)"),
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities"
    ],
)
