#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup

setup_config = dict(
    name="obspyDMT",
    version="0.3.0",
    author="Kasra Hosseini",
    author_email="hosseini@geophysik.uni-muenchen.de",
    description=("Retrieving, Processing and Management of Massive Seismic "
                 "Data (Serial and Parallel)"),
    long_description=(
        "obspyDMT (ObsPy Data Management Tool) is a command line tool for "
        "retrieving, processing and management of massive seismic data in a "
        "fully automatic way which could be run in serial or in parallel. "
        "Moreover, complementary processing and managing tools have been "
        "designed and introduced in addition to the obspyDMT options. Because "
        "of the modular nature, different functionalities could be added "
        " easily and/or each obspyDMT can be used as a module for other "
        "programs."),
    install_requires=[
        "obspy>=0.8.3",
        "pprocess"],
    packages=["obspyDMT"],
    package_dir={"obspyDMT":  "obspyDMT"},
    keywords=["obspyDMT", "ObsPy", "Seismology"],
    entry_points={
        'console_scripts': [
            'obspyDMT = obspyDMT.obspyDMT:main'
        ],
    },
    url="https://github.com/kasra-hosseini/obspyDMT",
    download_url="https://github.com/kasra-hosseini/obspyDMT.git",
    license="GNU General Public License, version 3 (GPLv3)",
    platforms="OS Independent",
    classifiers=[
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
        ("License :: OSI Approved :: "
            "GNU Library or General Public License (GPL)"),
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules"],
)

if __name__ == "__main__":
    setup(**setup_config)
