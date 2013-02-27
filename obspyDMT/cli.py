#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Command line interface to obspyDMT.

:copyright:
    Kasra Hosseini (hosseini@geophysik.uni-muenchen.de),
    Lion Krischer (krischer@geophysik.uni-muenchen.de), 2011-2013

:license:
    GNU General Public License, Version 3
    (http://www.gnu.org/licenses/gpl-3.0-standalone.html)
"""
import argparse
import colorama
from datetime import datetime
import logging
import sys

from obspyDMT import VERSION


class Logger(object):
    """
    Simple logging class printing to the screen in colors as well as to a file.
    """
    def __init__(self, log_filename):
        FORMAT = "[%(asctime)-15s] %(message)s"
        logging.basicConfig(filename=log_filename, level=logging.DEBUG,
            format=FORMAT)
        self.logger = logging.getLogger("obspyDMT")

    def critical(self, msg):
        print(colorama.Fore.WHITE + colorama.Back.RED +
            self._format_message(msg) + colorama.Style.RESET_ALL)
        self.logger.critical(msg)

    def error(self, msg):
        print(colorama.Fore.RED + self._format_message(msg) +
            colorama.Style.RESET_ALL)
        self.logger.error(msg)

    def warning(self, msg):
        print(colorama.Fore.YELLOW + self._format_message(msg) +
            colorama.Style.RESET_ALL)
        self.logger.warning(msg)

    def info(self, msg):
        print(self._format_message(msg))
        self.logger.info(msg)

    def debug(self, msg):
        print(self._format_message(msg))
        self.logger.debug(msg)

    def _format_message(msg):
        return "[%s] %s" % (datetime.now(), msg)


def parse_arguments():
    """
    Parses command line options and returns the parse object.
    """
    # Define some formats used in the argument parser.
    def rectangular_selection(string):
        """
        Define a rectangular selection format.
        """
        msg = ("'%s' is not a valid rectangle. Needs to be given as "
            "'<lonmin>/<lonmax>/<latmin>/<latmax>'")
        try:
            values = map(float, string.split("/"))
        except:
            raise argparse.ArgumentTypeError(msg % string)
        if len(values) != 4:
            raise argparse.ArgumentTypeError(msg % string)
        return values

    def circular_selection(string):
        """
        Define a circular section format.
        """
        msg = ("'%s' is not a valid circular selection. Needs to be given as "
            "'<lon>/<lat>/<rmin>/<rmax>'")
        try:
            values = map(float, string.split("/"))
        except:
            raise argparse.ArgumentTypeError(msg % string)
        if len(values) != 4 or \
                not (-180.0 <= values[0] <= 180.0) or \
                not (-90.0 <= values[1] <= 90.0):
            raise argparse.ArgumentTypeError(msg % string)
        return values

    parser = argparse.ArgumentParser(
        description="Download and manage large seismological datasets",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--version", action="store_true",
        help="output version information and exit")

    # Group all options related to station selection
    station_options = parser.add_argument_group("Station selection options")
    station_options.add_argument("--station_pattern", default="*.*",
        help="station restriction, syntax: network.station (eg: [TA,BW].A* "
        "will search for all stations in networks TA and BW, starting with A")
    station_options.add_argument("--channel_priority",
        default=["HH[Z,N,E]", "BH[Z,N,E]", "MH[Z,N,E]", "EH[Z,N,E]",
            "LH[Z,N,E]"],
        help="For each station all channels matching the first pattern in "
        "the list will be retrieved. If one or more channels are found it "
        "stops. Otherwise it will attempt to retrieve channels matching the "
        "next pattern. And so on.")
    station_options.add_argument("--station_rect", type=rectangular_selection,
        default="-180.0/+180.0/-90.0/+90.0",
        help="Search for stations in the defined rectangular region. "
            "GMT syntax: <lonmin>/<lonmax>/<latmin>/<latmax>")
    station_options.add_argument("--station_circle", type=circular_selection,
        help="epicentral distance circle, radius is given in degree. "
        "Syntax: <lon>/<lat>/<rmin>/<rmax>")

    # Group with all options related to event search.
    event_options = parser.add_argument_group("Event search options")
    event_options.add_argument("--min_mag", type=float, default=5.5,
        help="minimum magnitude")
    event_options.add_argument("--max_mag", type=float, default=9.9,
        help="maximum magnitude")
    event_options.add_argument("--event_rect", type=rectangular_selection,
        default="-180.0/+180.0/-90.0/+90.0",
        help="Search for events in the defined rectangular region. "
            "GMT syntax: <lonmin>/<lonmax>/<latmin>/<latmax>")
    event_options.add_argument("--event_circle", type=circular_selection,
        help="epicentral distance circle, radius is given in degree. "
        "Syntax: <lon>/<lat>/<rmin>/<rmax>")
    event_options.add_argument("--min_depth", type=float, default=-10,
        help="minimum depth in km. Values increase positively with depth")
    event_options.add_argument("--max_depth", type=float, default=6000,
        help="maximum depth in km. Values increase positively with depth")
    event_options.add_argument("--catalog", type=str, default="EMSC",
        choices=["EMSC", "IRIS", "GCMT", "TEST", "ISC", "UofW", "NEIC", "PDE"],
        help="event catalog to query, one of EMSC, IRIS - contains the "
        "following, which can also be chosen seperately: ANF, GCMT, "
        "TEST, ISC, UofW, NEIC, PDE")
    event_options.add_argument("--mag_type", type=str, default="Mw",
        help="magnitude type. Available options depend on the catalog and "
            "include Ml/MD, mb, Mw, ...")

    args = parser.parse_args()

    # Print help message if no argument is given.
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    return args


def __main__():
    # Parse the command line arguments.
    args = parse_arguments()
    # In case only the version is requested, print it and exit.
    if args.version:
        print("obspyDMT v%s" % VERSION)
        sys.exit(0)

    # Init logger.
    logger = Logger(log_filename="obspyDMT.log")
