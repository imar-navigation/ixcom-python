#!/usr/bin/env python3
"""Setup script for xcom library"""

from setuptools import setup
import os
import sys

if sys.version_info[0] < 3 or (sys.version_info[0] == 3 and sys.version_info[1] < 6):
    sys.exit('Sorry, Python < 3.6 is not supported')

if __name__ == '__main__':

    readmePath = os.path.join(os.path.dirname(__file__), 'README.md')
    long_description = open(readmePath, "rt").read()

    setup(name='ixcom',
          version='1.1.1',
          description='Library for communicating with xcom devices over network',
          author='iMAR Navigation GmbH',
          author_email='support@imar-navigation.de',
          url='http://www.imar-navigation.de',
          keywords=['XCOM', 'Inertial navigation', 'INS', 'iMAR', 'iNAT', 'GNSS', 'GPS', 'AHRS'],
          packages=['ixcom'],
          entry_points={
            'console_scripts': [
                        'configdump2txt = ixcom.cmdline:configdump2txt',
                        'monitor2xcom = ixcom.cmdline:monitor2xcom',
                        'xcom_lookup = ixcom.cmdline:xcom_lookup',
                        'split_config = ixcom.cmdline:split_config',
                                ],
                        },
          install_requires=[
                    'numpy>=1.16.2',
                ],
          classifiers=[
                "Programming Language :: Python :: 3.6",
                "License :: OSI Approved :: MIT License",
                "Operating System :: OS Independent",
                ],
          long_description=long_description,
          long_description_content_type="text/markdown",
          project_urls={
            "Documentation": "https://ixcom.readthedocs.io/en/latest/",
            "Source Code":   "https://github.com/imar-navigation/ixcom-python",
            },
          )
