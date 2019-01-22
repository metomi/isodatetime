# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Copyright (C) 2013-2019 British Crown (Met Office) & Contributors.
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
import sys
from setuptools import setup
from isodatetime import __version__
# overriding setuptools command
# https://stackoverflow.com/a/51294311
from setuptools.command.bdist_rpm import bdist_rpm as bdist_rpm_original
# to parse pytest command arguments
# https://docs.pytest.org/en/2.8.7/goodpractices.html#manual-integration
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ""

    def run_tests(self):
        import shlex
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(shlex.split(self.pytest_args))
        sys.exit(errno)


def read(fname):
    """Utility function to read the README file.

    Used for the long_description. It's nice, because now 1) we have a top
    level README file and 2) it's easier to type in the README file than to
    put a raw string in below ..."""
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


class bdist_rpm(bdist_rpm_original):

    def run(self):
        """Before calling the original run method, let's change the
        distribution name to create an RPM for python-isodatetime."""
        self.distribution.metadata.name = "python-isodatetime"
        self.distribution.metadata.version = __version__
        super().run()


setup(
    name="isodatetime",
    version='1!' + __version__,
    author="Met Office",
    author_email="metomi@metoffice.gov.uk",
    cmdclass={
        "bdist_rpm": bdist_rpm,
        "pytest": PyTest
    },
    description=("Python ISO 8601 date time parser" +
                 " and data model/manipulation utilities"),
    license="LGPLv3",
    keywords="isodatetime datetime iso8601 date time parser",
    url="https://github.com/metomi/isodatetime",
    packages=['isodatetime'],
    long_description=read('README.md'),
    long_description_content_type="text/markdown",
    platforms='any',
    setup_requires=['pytest-runner'],
    tests_require=['coverage', 'pytest', 'pytest-cov', 'pytest-env'],
    install_requires=[],
    python_requires='>=3.4, <3.8',
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        ("License :: OSI Approved" +
         " :: GNU Lesser General Public License v3 (LGPLv3)"),
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities"
    ],
    entry_points={
        'console_scripts': ['isodatetime=isodatetime.main:main'],
    },
)
