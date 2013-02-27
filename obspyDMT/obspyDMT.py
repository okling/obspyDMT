#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
obspyDMT main program

:copyright:
    Kasra Hosseini (hosseini@geophysik.uni-muenchen.de),
    Lion Krischer (krischer@geophysik.uni-muenchen.de),
    2011-2013
:license:
    GNU General Public License, Version 3
    (http://www.gnu.org/licenses/gpl-3.0-standalone.html)
"""
import argparse
from datetime import datetime
import os
import sys
import time

#from obspyDMT.download_cores import IRIS_download_core
#from obspyDMT.util import get_folder_size, send_email, XML_list_avail
#from obspyDMT.event_file_handler import quake_info
#from obspyDMT.station_file_handler import read_station_event, rm_duplicate

VERSION = "0.4.0a"


def obspyDMT(*args, **kwargs):
    """
    """
    #parser = 1
    #helpmsg = "the path where obspyDMT will store the data " + \
        #"[Default: './obspyDMT-data']"
    #parser.add_option("--datapath", action="store", dest="datapath",
                      #help=helpmsg)

    #helpmsg = "start time, syntax: Y-M-D-H-M-S (eg: " + \
        #"'2010-01-01-00-00-00') or just Y-M-D [Default: 10 days ago]"
    #parser.add_option("--min_date", action="store",
                      #dest="min_date", help=helpmsg)

    #helpmsg = "end time, syntax: Y-M-D-H-M-S (eg: " + \
        #"'2011-01-01-00-00-00') or just Y-M-D [Default: 5 days ago]"
    #parser.add_option("--max_date", action="store",
                      #dest="max_date", help=helpmsg)

    #helpmsg = "Just retrieve the event information and create an event " + \
        #"archive."
    #parser.add_option("--event_info", action="store_true",
                      #dest="event_info", help=helpmsg)


    #helpmsg = "time interval for dividing the continuous request. " + \
        #"[Default: 86400 sec (1 day)]"
    #parser.add_option("--interval", action="store", dest="interval",
                      #help=helpmsg)

    #helpmsg = "Number of processors to be used in --req_parallel. [Default: 4]"
    #parser.add_option("--req_np", action="store", dest="req_np", help=helpmsg)

    #helpmsg = "retrieve the waveform. [Default: 'Y']"
    #parser.add_option("--waveform", action="store",
                      #dest="waveform", help=helpmsg)

    #helpmsg = "retrieve the response file. [Default: 'Y']"
    #parser.add_option("--response", action="store",
                      #dest="response", help=helpmsg)

    #helpmsg = "retrieve the PAZ."
    #parser.add_option("--paz", action="store_true",
                      #dest="paz", help=helpmsg)

    #helpmsg = "time parameter in seconds which determines how close " + \
                #"the time series data (waveform) will be cropped " + \
                #"before the origin time of the event. Default: 0.0 seconds."
    #parser.add_option("--preset", action="store",
                      #dest="preset", help=helpmsg)

    #helpmsg = "time parameter in seconds which determines how close " + \
                #"the time series data (waveform) will be cropped " + \
                #"after the origin time of the event. Default: 1800.0 seconds."
    #parser.add_option("--offset", action="store",
                      #dest="offset", help=helpmsg)

    #helpmsg = "search for all the stations within the defined " + \
                #"rectangle, GMT syntax: " + \
                #"<lonmin>/<lonmax>/<latmin>/<latmax>. May not be " + \
                #"used together with circular bounding box station " + \
                #"restrictions (station_circle) " + \
                #"[Default: -180.0/+180.0/-90.0/+90.0]"
    #parser.add_option("--station_rect", action="store",
                      #dest="station_rect", help=helpmsg)

    #helpmsg = "search for all the stations within the defined " + \
                #"circle, syntax: <lon>/<lat>/<rmin>/<rmax>. " + \
                #"May not be used together with rectangular " + \
                #"bounding box station restrictions (station_rect)." + \
                #" Currently, ArcLink does not support this option!"
    #parser.add_option("--station_circle", action="store",
                      #dest="station_circle", help=helpmsg)

    #helpmsg = "apply a bandpass filter to the data trace before " + \
                #"deconvolution ('None' if you do not need pre_filter), " + \
                #"syntax: '(f1,f2,f3,f4)' which are the four corner " + \
                #"frequencies of a cosine taper, one between f2 and f3 " + \
                #"and tapers to zero for f1 < f < f2 and f3 < f < f4. " + \
                #"[Default: '(0.008, 0.012, 3.0, 4.0)']"
    #parser.add_option("--pre_filt", action="store",
                      #dest="pre_filt", help=helpmsg)

    #helpmsg = "Instrument Correction (full response), using obspy modules"
    #parser.add_option("--ic_obspy_full", action="store",
                      #dest="ic_obspy_full", help=helpmsg)

    #helpmsg = "Instrument Correction (full response), using SAC"
    #parser.add_option("--ic_sac_full", action="store_true",
                      #dest="ic_sac_full", help=helpmsg)

    #helpmsg = "Instrument Correction (Poles And Zeros), " + \
                #"using SAC (for IRIS) and obspy (for ArcLink)"
    #parser.add_option("--ic_paz", action="store_true",
                      #dest="ic_paz", help=helpmsg)

    #helpmsg = "correct the raw waveforms for DIS (m), VEL (m/s) or " + \
                #"ACC (m/s^2). [Default: DIS]"
    #parser.add_option("--corr_unit", action="store",
                      #dest="corr_unit", help=helpmsg)

    ## parse command line options
    #(options, args) = parser.parse_args()

    #return options, args, parser


def main():
    """
    XXX: Add documentation.
    """
    global t1_pro, t1_str

    t1_pro = time.time()
    t1_str = datetime.now()

    status = obspyDMT()

    input, events = None

    size = get_folder_size(input['datapath'])
    size /= 1024 ** 2

    t_pro = time.time() - t1_pro

    print "\n\n--------------------------------------------------"
    print "Info:"
    print "* The following folder contains %f MB of data." % (size)
    print input['datapath']
    print "\n* Total time:"
    print "%f sec" % (t_pro)
    print "--------------------------------------------------"
   # -------------------------------------------------------------------
    Period = input['min_date'].split('T')[0] + '_' + \
                input['max_date'].split('T')[0] + '_' + \
                str(input['min_mag']) + '_' + str(input['max_mag'])
    eventpath = os.path.join(input['datapath'], Period)

    address = []
    for event in events:
        address.append(os.path.join(eventpath, event['event_id']))
   # -------------------------------------------------------------------
    if address != []:
        print "* Address of the stored events:"
        for i in range(len(events)):
            print address[i]
        print 50 * "-"

    sys.exit(status)


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
    args = parse_arguments()
    if args.version:
        print("obspyDMT v%s" % VERSION)
        sys.exit(0)


if __name__ == "__main__":
    __main__()
