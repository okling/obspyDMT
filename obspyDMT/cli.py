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
from obspy import UTCDateTime
import os
import shelve
import sys


from obspyDMT import VERSION
from obspyDMT.availability import get_availability
from obspyDMT.waveforms import download_waveforms


class Logger(object):
    """
    Simple logging class printing to the screen in color as well as to a file.
    """
    def __init__(self, log_filename):
        FORMAT = "[%(asctime)-15s] %(levelname)s: %(message)s"
        logging.basicConfig(filename=log_filename, level=logging.DEBUG,
            format=FORMAT)
        self.logger = logging.getLogger("obspyDMT")

    def critical(self, msg):
        print(colorama.Fore.WHITE + colorama.Back.RED +
            self._format_message("CRITICAL", msg) + colorama.Style.RESET_ALL)
        self.logger.critical(msg)

    def error(self, msg):
        print(colorama.Fore.RED + self._format_message("ERROR", msg) +
            colorama.Style.RESET_ALL)
        self.logger.error(msg)

    def warning(self, msg):
        print(colorama.Fore.YELLOW + self._format_message("WARNING", msg) +
            colorama.Style.RESET_ALL)
        self.logger.warning(msg)

    def info(self, msg):
        print(self._format_message("INFO", msg))
        self.logger.info(msg)

    def debug(self, msg):
        print(self._format_message("DEBUG", msg))
        self.logger.debug(msg)

    def _format_message(self, prefix, msg):
        return "[%s] %s: %s" % (datetime.now(), prefix, msg)


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

    def string_list(string):
        """
        Define a list of strings, seperated by a forward slash.
        """
        values = string.split("/")
        return values

    def fraction(string):
        """
        Defines a fraction. Must be convertible to a float and between 0.0 and
        1.0.
        """
        value = float(string)
        if 0.0 <= value <= 1.0:
            return value
        msg = "'%s' is not between 0.0 and 1.0" % string
        raise argparse.ArgumentTypeError(msg % msg)

    parser = argparse.ArgumentParser(
        description="Download and manage large seismological datasets",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("folder", type=str,
        help="Folder where files are saved")

    parser.add_argument("--version", action="store_true",
        help="output version information and exit")
    parser.add_argument("--arclink_user", type=str, required=True,
        help="ArcLink user email. Please provide a valid one.")

    # Group waveform download options
    waveform_options = parser.add_argument_group("Waveform Download Options")
    waveform_options.add_argument("--minimumlength", default=0.9,
        type=fraction, help="The minimum length of a waveform segment as a "
        "fraction of the requested length")
    waveform_options.add_argument("--format", default="mseed",
        choices=["mseed", "sac", "gse2", "seisan", "segy"],
        help="Final waveform file format")

    # Group all options related to station selection
    station_options = parser.add_argument_group("Station Selection Options")
    station_options.add_argument("--station_pattern", default="*.*",
        help="station restriction, syntax: network.station (eg: [TA,BW].A* "
        "will search for all stations in networks TA and BW, starting with A")
    station_options.add_argument("--channel_priority", type=string_list,
        default="HH[Z,N,E]/BH[Z,N,E]/MH[Z,N,E]/EH[Z,N,E]/LH[Z,N,E]",
        help="For each station all channels matching the first pattern in "
        "the list will be retrieved. If one or more channels are found it "
        "stops. Otherwise it will attempt to retrieve channels matching the "
        "next pattern. And so on.")
    station_options.add_argument("--station_rect", type=rectangular_selection,
        default="-180.0/+180.0/-90.0/+90.0",
        help="Search for stations in the defined rectangular region. "
            "GMT syntax: <lonmin>/<lonmax>/<latmin>/<latmax>")
    station_options.add_argument("--starttime", type=UTCDateTime,
        default=UTCDateTime() - 10 * 86400,
        help="Starttime for download request")
    station_options.add_argument("--endtime", type=UTCDateTime,
        default=UTCDateTime() - 10 * 86400 + 600,
        help="Endtime for download request")
    #station_options.add_argument("--station_circle", type=circular_selection,
        #help="epicentral distance circle, radius is given in degree. "
        #"Syntax: <lon>/<lat>/<rmin>/<rmax>")

    # Group with all options related to event search.
    #event_options = parser.add_argument_group("Event search options")
    #event_options.add_argument("--min_mag", type=float, default=5.5,
        #help="minimum magnitude")
    #event_options.add_argument("--max_mag", type=float, default=9.9,
        #help="maximum magnitude")
    #event_options.add_argument("--event_rect", type=rectangular_selection,
        #default="-180.0/+180.0/-90.0/+90.0",
        #help="Search for events in the defined rectangular region. "
            #"GMT syntax: <lonmin>/<lonmax>/<latmin>/<latmax>")
    #event_options.add_argument("--event_circle", type=circular_selection,
        #help="epicentral distance circle, radius is given in degree. "
        #"Syntax: <lon>/<lat>/<rmin>/<rmax>")
    #event_options.add_argument("--min_depth", type=float, default=-10,
        #help="minimum depth in km. Values increase positively with depth")
    #event_options.add_argument("--max_depth", type=float, default=6000,
        #help="maximum depth in km. Values increase positively with depth")
    #event_options.add_argument("--catalog", type=str, default="EMSC",
        #choices=["EMSC", "IRIS", "GCMT", "TEST", "ISC", "UofW", "NEIC", "PDE"],
        #help="event catalog to query, one of EMSC, IRIS - contains the "
        #"following, which can also be chosen seperately: ANF, GCMT, "
        #"TEST, ISC, UofW, NEIC, PDE")
    #event_options.add_argument("--mag_type", type=str, default="Mw",
        #help="magnitude type. Available options depend on the catalog and "
            #"include Ml/MD, mb, Mw, ...")

    # Print help message if no argument is given.
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    return args


def _init_folders(*args):
    """
    Every folder in args will be created if it does not already exists.
    """
    for folder in args:
        if os.path.exists(folder):
            continue
        os.makedirs(folder)


def __main__():
    # Parse the command line arguments.
    args = parse_arguments()
    # In case only the version is requested, print it and exit.
    if args.version:
        print("obspyDMT v%s" % VERSION)
        sys.exit(0)

    # Init all necessary folders.
    waveform_folder = os.path.join(args.folder, "waveforms")
    station_folder = os.path.join(args.folder, "stations")
    temp_folder = os.path.join(args.folder, ".temp")
    shelve_file = os.path.join(temp_folder, "SHELVE")
    _init_folders(args.folder, waveform_folder, station_folder, temp_folder)

    # Any previously existing persistence shelve file is only valid if no
    # arguments have been changed. Therefore check the existing shelve and
    # compare the arguments.
    dmt_shelve = shelve.open(shelve_file)
    if "args" in dmt_shelve:
        # If they are not identical any cached values are potentially invalid.
        if args != dmt_shelve["args"]:
            dmt_shelve.clear()
    if "args" not in dmt_shelve:
        dmt_shelve["args"] = args
    dmt_shelve.close()

    # Init logger.
    logger = Logger(log_filename=os.path.join(args.folder, "log.txt"))

    # Log some basic information
    logger.info(70 * "=")
    logger.info(70 * "=")
    logger.info("Launching obspyDMT version %s" % VERSION)
    logger.info("Arguments:")
    keys = sorted(args.__dict__.keys())
    for key in keys:
        logger.info("\t%s: %s" % (str(key), str(getattr(args, key))))

    dmt_shelve = shelve.open(shelve_file)
    if "channels" in dmt_shelve:
        logger.info("Loading channel availability from cache...")
        channels = dmt_shelve["channels"]
        logger.info("Loaded %i unique channels." % len(channels))
    else:
        # First get all channels.
        channels = get_availability(args.station_rect[2], args.station_rect[3],
            args.station_rect[0], args.station_rect[1], args.starttime,
            args.endtime, arclink_user=args.arclink_user,
            station_pattern=args.station_pattern, logger=logger)
        if not channels:
            msg = "No matching channels found. Program will terminate."
            logger.critical(msg)
            dmt_shelve.close()
            sys.exit(1)
        dmt_shelve["channels"] = channels
    dmt_shelve.close()

    def get_channel_filename(channel_id):
        """
        Get the filename given a seed channel id.

        File format and other things will be available via closures.
        """
        filename = "%s.%s" % (channel_id, args.format)
        foldername = "%s_%s" % (args.starttime.strftime("%Y-%m-%dT%H-%M-%S"),
            args.endtime.strftime("%Y-%m-%dT%H-%M-%S"))
        return os.path.join(waveform_folder, foldername, filename)

    # Now get a list of those channels that still need downloading.
    channels_to_download = []
    for chan in channels.iterkeys():
        filename = get_channel_filename(chan)
        if os.path.exists(filename):
            continue
        channels_to_download.append(chan)

    def save_channel(stream):
        """
        Save a stream containing a single trace.
        """
        # Just a safety measure. This should not happen.
        if len(stream) != 1:
            msg = "Only streams containing one trace will be saved."
            logger.error(msg)
            return

    logger.info("Downloading %i waveform channels..." %
        len(channels_to_download))
    # Actually download the data.
    download_waveforms(channels_to_download, args.starttime, args.endtime,
        args.minimumlength, save_stream_fct=save_channel,
        arclink_user=args.arclink_user, logger=logger)
