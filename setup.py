#!/usr/bin/env python3
"""Setup script for xcom library"""

##############################################################################
#
#    Copyright (C) iMAR Navigation GmbH, 2016
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from setuptools import setup
import os
import sys

if sys.version_info[0] < 3 or (sys.version_info[0] == 3 and sys.version_info[1] < 6):
    sys.exit('Sorry, Python < 3.6 is not supported')

if __name__ == '__main__':

    readmePath = os.path.join(os.path.dirname(__file__), 'README.md')
    long_description = open(readmePath, "rt").read()

    setup(name='xcom',
          version='1.0.0',
          description='Library for communicating with xcom devices over network',
          author='iMAR Navigation GmbH',
          author_email='support@imar-navigation.de',
          url='http://www.imar-navigation.de',
          keywords=['XCOM'],
          packages=['xcom'],
          install_requires=[
                    'numpy>=1.16.2',
                ],
          classifiers=[
                "Programming Language :: Python :: 3.6",
                "License :: OSI Approved :: MIT License",
                "Operating System :: OS Independent",
                ],
          )
