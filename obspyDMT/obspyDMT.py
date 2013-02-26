#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
obspyDMT main program

:copyright:
    Kasra Hosseini (hosseini@geophysik.uni-muenchen.de), 2012-2013
:license:
    GNU General Public License, Version 3
    (http://www.gnu.org/licenses/gpl-3.0-standalone.html)
"""
import argparse
import commands
from datetime import datetime
import fnmatch
import matplotlib
import numpy as np
import obspy
from obspy import read, UTCDateTime
from obspy.signal import seisSim, invsim
from optparse import OptionParser
import pickle
import pprocess
import os
import scipy
import shutil
import subprocess
import sys
import time

from obspyDMT.download_cores import IRIS_download_core
from obspyDMT.util import get_folder_size, send_email, XML_list_avail
from obspyDMT.event_file_handler import quake_info
from obspyDMT.station_file_handler import read_station_event, rm_duplicate


def obspyDMT(**kwargs):
    """
    obspyDMT: is the function dedicated to the main part of the code.

    To run this program you have different options:
    1. External INPUT file ---> following files should be in the same
       folder as obspyDMT:
    * INPUT.cfg
    2. Command line (Please type "./obspyDMT.py --help" for more information)
    3. Imported and called with appropriate keyword arguments in other scripts.
    * There are no real checks for the keywords, so be sure to get them right.

    Parameters
    ----------
    :type datapath: str, optional
    :param datapath:
    :type events: str, optional
    :param end: End time of event query timeframe. obspy.core.UTCDateTime
        recognizable string.

    .. rubric:: Example

        >>> from obspyDMT import obspyDMT
        >>> obspyDMT(datapath="van", magmin=7, start="2011-10-23", force=True)
        Downloading NERIES eventlist...
        done.
        Received 1 event(s) from NERIES.
        Downloading ArcLink inventory data...
        (...)

    .. rubric:: Notes

         See obspyDMT's help functions (command line: obspyDMT -h and
         obspyDMT -H) as well as the obspyDMT manual (available on the ObsPy
         SVN server) for further documentation.
    """

    print '\n------------------------------------------------------------' + \
        '---------------------'
    print '\t\t' + 'obspyDMT (ObsPy Data Management Tool)' + '\n'
    print '\t' + 'Automatic tool for Downloading, Processing and Management'
    print '\t\t\t' + 'of Large Seismic Datasets'
    print '\n'
    print ':copyright:'
    print 'The ObsPy Development Team (devs@obspy.org)' + '\n'
    print 'Developed by Kasra Hosseini'
    print 'email: hosseini@geophysik.uni-muenchen.de' + '\n'
    print ':license:'
    print 'GNU General Public License, Version 3'
    print '(http://www.gnu.org/licenses/gpl-3.0-standalone.html)'
    print '------------------------------------------------------------' + \
        '---------------------'

    # global variables
    global input, events

    # ------------------Parsing command-line options--------------------
    (options, args, parser) = command_parse()

    # ------------------Read INPUT file (Parameters)--------------------
    if options.type == 'file':
        read_input_file()
    else:
        read_input_command(parser, **kwargs)

    # ------------------Getting List of Events/Continuous requests------
    if input['get_events'] == 'Y':
        get_Events(input, request='event-based')

    if input['get_continuous'] == 'Y':
        get_Events(input, request='continuous')

    # ------------------Seismicity--------------------------------------
    if input['seismicity'] == 'Y':
        seismicity(input, events)

    # ------------------IRIS--------------------------------------------
    if input['IRIS'] == 'Y':

        print '\n********************************************************'
        print 'IRIS -- Download waveforms, response files and meta-data'
        print '********************************************************'

        IRIS_network(input)

    # ------------------Arclink-----------------------------------------
    if input['ArcLink'] == 'Y':

        print '\n***********************************************************'
        print 'ArcLink -- Download waveforms, response files and meta-data'
        print '***********************************************************'

        ARC_network(input)

    # ------------------IRIS-Updating-----------------------------------
    if input['iris_update'] != 'N':

        print '\n*********************'
        print 'IRIS -- Updating Mode'
        print '*********************'

        IRIS_update(input, address=input['iris_update'])

    # ------------------ArcLink-Updating--------------------------------
    if input['arc_update'] != 'N':

        print '\n************************'
        print 'ArcLink -- Updating Mode'
        print '************************'

        ARC_update(input, address=input['arc_update'])

    # ------------------IRIS-instrument---------------------------------
    if input['iris_ic'] != 'N' or input['iris_ic_auto'] == 'Y':

        print '\n*****************************'
        print 'IRIS -- Instrument Correction'
        print '*****************************'

        IRIS_ARC_IC(input, clients='iris')

    # ------------------Arclink-instrument------------------------------
    if input['arc_ic'] != 'N' or input['arc_ic_auto'] == 'Y':

        print '\n********************************'
        print 'ArcLink -- Instrument Correction'
        print '********************************'

        IRIS_ARC_IC(input, clients='arc')

    # ------------------IRIS-merge--------------------------------------
    if input['iris_merge'] != 'N' or input['iris_merge_auto'] == 'Y':

        print '\n*****************************'
        print 'IRIS -- Merging the waveforms'

        IRIS_ARC_merge(input, clients='iris')

    # ------------------ArcLink-merge-----------------------------------
    if input['arc_merge'] != 'N' or input['arc_merge_auto'] == 'Y':

        print '\n********************************'
        print 'ArcLink -- Merging the waveforms'

        IRIS_ARC_merge(input, clients='arc')

    # ------------------PLOT--------------------------------------------
    for i in ['plot_se', 'plot_sta', 'plot_ev', 'plot_ray', 'plot_ray_gmt',
              'plot_epi', 'plot_dt']:
        if input[i] != 'N':

            print '\n*********************'
            print 'Start the PLOT module'
            print '*********************'

            if input['plot_all'] == 'Y' or input['plot_iris'] == 'Y':
                PLOT(input, clients='iris')
            if input['plot_arc'] == 'Y':
                PLOT(input, clients='arc')

    # ------------------Email-------------------------------------------
    if input['email'] != 'N':

        print '\n*********************************************'
        print 'Sending email to the following email-address:'
        print input['email']
        print '*********************************************'

        global t1_pro, t1_str
        t2_pro = time.time()
        t2_str = datetime.now()
        t_pro = t2_pro - t1_pro
        msg = "Request at: \n" + str(t1_str) + "\n\nFinished at \n" + \
            str(t2_str) + "\n\n" + "Total time: " + "\n" + str(t_pro)
        send_email(input["email"], msg)


def parse_commands():
    """
    Parses command line options and returns the parse object.
    """
    parser = argparse.ArgumentParser(
        description="Download and manage large seismological datasets")

    parser.add_argument("--version", action="store_true",
            help="output version information and exit")

    args = parser.parse_args()
    return args


def command_parse():
    """
    Parsing command-line options.
    """
    # create command line option parser
    parser = OptionParser("%prog [options]")

    helpmsg = "show the obspyDMT version and exit"
    parser.add_option("--version", action="store_true",
                      dest="version", help=helpmsg)

    helpmsg = "check all the dependencies and their installed versions " + \
        "on the local machine and exit"
    parser.add_option("--check", action="store_true",
                      dest="check", help=helpmsg)

    helpmsg = "Run a quick tour!"
    parser.add_option("--tour", action="store_true",
                      dest="tour", help=helpmsg)

    helpmsg = "type of the input ('command' or 'file') to be read by " + \
        "obspyDMT. Please note that for \"--type 'file'\" an " + \
        "external file ('INPUT.cfg') should exist in the same " + \
        "directory as obspyDMT.py [Default: command] "
    parser.add_option("--type", action="store",
                      dest="type", help=helpmsg)

    helpmsg = "if the datapath is found deleting it before running obspyDMT."
    parser.add_option("--reset", action="store_true",
                      dest="reset", help=helpmsg)

    helpmsg = "the path where obspyDMT will store the data " + \
        "[Default: './obspyDMT-data']"
    parser.add_option("--datapath", action="store", dest="datapath",
                      help=helpmsg)

    helpmsg = "start time, syntax: Y-M-D-H-M-S (eg: " + \
        "'2010-01-01-00-00-00') or just Y-M-D [Default: 10 days ago]"
    parser.add_option("--min_date", action="store",
                      dest="min_date", help=helpmsg)

    helpmsg = "end time, syntax: Y-M-D-H-M-S (eg: " + \
        "'2011-01-01-00-00-00') or just Y-M-D [Default: 5 days ago]"
    parser.add_option("--max_date", action="store",
                      dest="max_date", help=helpmsg)

    helpmsg = "event catalog (EMSC or IRIS). [Default: 'EMSC']"
    parser.add_option("--event_catalog", action="store",
                      dest="event_catalog", help=helpmsg)

    helpmsg = "magnitude type. Some common types (there are many) " + \
        "include 'Ml' (local/Richter magnitude), " + \
        "'Ms' (surface magnitude), 'mb' (body wave magnitude), " + \
        "'Mw' (moment magnitude). [Default: 'Mw']"
    parser.add_option("--mag_type", action="store",
                      dest="mag_type", help=helpmsg)

    helpmsg = "minimum magnitude. [Default: 5.5]"
    parser.add_option("--min_mag", action="store",
                      dest="min_mag", help=helpmsg)

    helpmsg = "maximum magnitude. [Default: 9.9]"
    parser.add_option("--max_mag", action="store",
                      dest="max_mag", help=helpmsg)

    helpmsg = "minimum depth. [Default: +10.0 (above the surface!)]"
    parser.add_option("--min_depth", action="store",
                      dest="min_depth", help=helpmsg)

    helpmsg = "maximum depth. [Default: -6000.0]"
    parser.add_option("--max_depth", action="store",
                      dest="max_depth", help=helpmsg)

    helpmsg = "search for all the events within the defined rectangle, " + \
        "GMT syntax: <lonmin>/<lonmax>/<latmin>/<latmax> " + \
        "[Default: -180.0/+180.0/-90.0/+90.0]"
    parser.add_option("--event_rect", action="store", dest="event_rect",
                      help=helpmsg)

    helpmsg = "search for all the events within the defined " + \
        "circle, syntax: <lon>/<lat>/<rmin>/<rmax>. " + \
        "May not be used together with rectangular " + \
        "bounding box event restrictions (event_rect). " + \
        "[currently just IRIS support this option]"
    parser.add_option("--event_circle", action="store",
                      dest="event_circle", help=helpmsg)

    helpmsg = "maximum number of events to be requested. [Default: 2500]"
    parser.add_option("--max_result", action="store",
                      dest="max_result", help=helpmsg)

    helpmsg = "Just retrieve the event information and create an event " + \
        "archive."
    parser.add_option("--event_info", action="store_true",
                      dest="event_info", help=helpmsg)

    helpmsg = "Create a seismicity map according to the event and " + \
        "location specifications."
    parser.add_option("--seismicity", action="store_true",
                      dest="seismicity", help=helpmsg)

    helpmsg = "event-based request (please refer to the tutorial). " + \
        "[Default: 'Y']"
    parser.add_option("--get_events", action="store", dest="get_events",
                      help=helpmsg)

    helpmsg = "continuous request (please refer to the tutorial)."
    parser.add_option("--continuous", action="store_true",
                      dest="get_continuous", help=helpmsg)

    helpmsg = "time interval for dividing the continuous request. " + \
        "[Default: 86400 sec (1 day)]"
    parser.add_option("--interval", action="store", dest="interval",
                      help=helpmsg)

    helpmsg = "Parallel waveform/response/paz request"
    parser.add_option("--req_parallel", action="store_true",
                      dest="req_parallel", help=helpmsg)

    helpmsg = "Number of processors to be used in --req_parallel. [Default: 4]"
    parser.add_option("--req_np", action="store", dest="req_np", help=helpmsg)

    helpmsg = "using the IRIS bulkdataselect Web service. Since this " + \
        "method returns multiple channels of time series data " + \
        "for specified time ranges in one request, it speeds up " + \
        "the waveform retrieving approximately by a factor of " + \
        "two. [RECOMMENDED]"
    parser.add_option("--iris_bulk", action="store_true",
                      dest="iris_bulk", help=helpmsg)

    helpmsg = "retrieve the waveform. [Default: 'Y']"
    parser.add_option("--waveform", action="store",
                      dest="waveform", help=helpmsg)

    helpmsg = "retrieve the response file. [Default: 'Y']"
    parser.add_option("--response", action="store",
                      dest="response", help=helpmsg)

    helpmsg = "retrieve the PAZ."
    parser.add_option("--paz", action="store_true",
                      dest="paz", help=helpmsg)

    helpmsg = "send request (waveform/response) to IRIS. [Default: 'Y']"
    parser.add_option("--iris", action="store",
                      dest="IRIS", help=helpmsg)

    helpmsg = "send request (waveform/response) to ArcLink. [Default: 'Y']"
    parser.add_option("--arc", action="store",
                      dest="ArcLink", help=helpmsg)

    helpmsg = "send request (waveform) to NERIES if ArcLink fails. [Default: 'N']"
    parser.add_option("--neries", action="store_true",
                      dest="NERIES", help=helpmsg)

    helpmsg = "SAC format for saving the waveforms. Station location " + \
                "(stla and stlo), station elevation (stel), " + \
                "station depth (stdp), event location (evla and evlo), " + \
                "event depth (evdp) and event magnitude (mag) " + \
                "will be stored in the SAC headers. [Default: 'Y'] "
    parser.add_option("--SAC", action="store",
                      dest="SAC", help=helpmsg)

    helpmsg = "MSEED format for saving the waveforms."
    parser.add_option("--mseed", action="store_true",
                      dest="mseed", help=helpmsg)

    helpmsg = "generate a data-time file for an IRIS request. " + \
                "This file shows the required time for each request " + \
                "and the stored data in the folder."
    parser.add_option("--time_iris", action="store_true",
                      dest="time_iris", help=helpmsg)

    helpmsg = "generate a data-time file for an ArcLink request. " + \
                "This file shows the required time for each request " + \
                "and the stored data in the folder."
    parser.add_option("--time_arc", action="store_true",
                      dest="time_arc", help=helpmsg)

    helpmsg = "time parameter in seconds which determines how close " + \
                "the time series data (waveform) will be cropped " + \
                "before the origin time of the event. Default: 0.0 seconds."
    parser.add_option("--preset", action="store",
                      dest="preset", help=helpmsg)

    helpmsg = "time parameter in seconds which determines how close " + \
                "the time series data (waveform) will be cropped " + \
                "after the origin time of the event. Default: 1800.0 seconds."
    parser.add_option("--offset", action="store",
                      dest="offset", help=helpmsg)

    helpmsg = "identity code restriction, syntax: net.sta.loc.cha " + \
                "(eg: TA.*.*.BHZ to search for all BHZ channels in " + \
                "TA network). [Default: *.*.*.*]"
    parser.add_option("--identity", action="store", dest="identity",
                        help=helpmsg)

    helpmsg = "network code. [Default: *]"
    parser.add_option("--net", action="store",
                      dest="net", help=helpmsg)

    helpmsg = "station code. [Default: *]"
    parser.add_option("--sta", action="store",
                      dest="sta", help=helpmsg)

    helpmsg = "location code. [Default: *]"
    parser.add_option("--loc", action="store",
                      dest="loc", help=helpmsg)

    helpmsg = "channel code. [Default: *]"
    parser.add_option("--cha", action="store",
                      dest="cha", help=helpmsg)

    helpmsg = "search for all the stations within the defined " + \
                "rectangle, GMT syntax: " + \
                "<lonmin>/<lonmax>/<latmin>/<latmax>. May not be " + \
                "used together with circular bounding box station " + \
                "restrictions (station_circle) " + \
                "[Default: -180.0/+180.0/-90.0/+90.0]"
    parser.add_option("--station_rect", action="store",
                      dest="station_rect", help=helpmsg)

    helpmsg = "search for all the stations within the defined " + \
                "circle, syntax: <lon>/<lat>/<rmin>/<rmax>. " + \
                "May not be used together with rectangular " + \
                "bounding box station restrictions (station_rect)." + \
                " Currently, ArcLink does not support this option!"
    parser.add_option("--station_circle", action="store",
                      dest="station_circle", help=helpmsg)

    helpmsg = "test the program for the desired number of requests, " + \
                "eg: '--test 10' will test the program for 10 requests. " + \
                "[Default: 'N']"
    parser.add_option("--test", action="store",
                      dest="test", help=helpmsg)

    helpmsg = "update the specified folder for IRIS, syntax: " + \
                "--iris_update address_of_the_target_folder. [Default: 'N']"
    parser.add_option("--iris_update", action="store",
                      dest="iris_update", help=helpmsg)

    helpmsg = "update the specified folder for ArcLink, syntax: " + \
                "--arc_update address_of_the_target_folder. [Default: 'N']"
    parser.add_option("--arc_update", action="store",
                      dest="arc_update", help=helpmsg)

    helpmsg = "update the specified folder for both IRIS and ArcLink, " + \
                "syntax: --update_all address_of_the_target_folder. " + \
                "[Default: 'N']"
    parser.add_option("--update_all", action="store",
                      dest="update_all", help=helpmsg)

    helpmsg = "apply instrument correction to the specified folder " + \
                "for the downloaded waveforms from IRIS, " + \
                "syntax: --iris_ic address_of_the_target_folder. " + \
                "[Default: 'N']"
    parser.add_option("--iris_ic", action="store",
                        dest="iris_ic", help=helpmsg)

    helpmsg = "apply instrument correction to the specified folder " + \
                "for the downloaded waveforms from ArcLink, " + \
                "syntax: --arc_ic address_of_the_target_folder. " + \
                "[Default: 'N']"
    parser.add_option("--arc_ic", action="store",
                        dest="arc_ic", help=helpmsg)

    helpmsg = "apply instrument correction automatically after " + \
                "downloading the waveforms from IRIS. [Default: 'Y']"
    parser.add_option("--iris_ic_auto", action="store",
                        dest="iris_ic_auto", help=helpmsg)

    helpmsg = "apply instrument correction automatically after " + \
                "downloading the waveforms from ArcLink. [Default: 'Y']"
    parser.add_option("--arc_ic_auto", action="store",
                        dest="arc_ic_auto", help=helpmsg)

    helpmsg = "apply instrument correction to the specified folder " + \
                "for all the waveforms (IRIS and ArcLink), " + \
                "syntax: --ic_all address_of_the_target_folder. [Default: 'N']"
    parser.add_option("--ic_all", action="store",
                        dest="ic_all", help=helpmsg)

    helpmsg = "do not apply instrument correction automatically. " + \
                "This is equivalent to: \"--iris_ic_auto N --arc_ic_auto N\""
    parser.add_option("--ic_no", action="store_true",
                        dest="ic_no", help=helpmsg)

    helpmsg = "Parallel Instrument Correction. "
    parser.add_option("--ic_parallel", action="store_true",
                        dest="ic_parallel", help=helpmsg)

    helpmsg = "Number of processors to be used in --ic_parallel. [Default: 20]"
    parser.add_option("--ic_np", action="store",
                        dest="ic_np", help=helpmsg)

    helpmsg = "Instrument Correction (full response), using obspy modules"
    parser.add_option("--ic_obspy_full", action="store",
                      dest="ic_obspy_full", help=helpmsg)

    helpmsg = "Instrument Correction (full response), using SAC"
    parser.add_option("--ic_sac_full", action="store_true",
                      dest="ic_sac_full", help=helpmsg)

    helpmsg = "Instrument Correction (Poles And Zeros), " + \
                "using SAC (for IRIS) and obspy (for ArcLink)"
    parser.add_option("--ic_paz", action="store_true",
                      dest="ic_paz", help=helpmsg)

    helpmsg = "apply a bandpass filter to the data trace before " + \
                "deconvolution ('None' if you do not need pre_filter), " + \
                "syntax: '(f1,f2,f3,f4)' which are the four corner " + \
                "frequencies of a cosine taper, one between f2 and f3 " + \
                "and tapers to zero for f1 < f < f2 and f3 < f < f4. " + \
                "[Default: '(0.008, 0.012, 3.0, 4.0)']"
    parser.add_option("--pre_filt", action="store",
                      dest="pre_filt", help=helpmsg)

    helpmsg = "correct the raw waveforms for DIS (m), VEL (m/s) or " + \
                "ACC (m/s^2). [Default: DIS]"
    parser.add_option("--corr_unit", action="store",
                      dest="corr_unit", help=helpmsg)

    helpmsg = "compress the raw-waveform files after applying " + \
                "instrument correction."
    parser.add_option("--zip_w", action="store_true",
                        dest="zip_w", help=helpmsg)

    helpmsg = "compress the response files after applying " + \
                "instrument correction."
    parser.add_option("--zip_r", action="store_true",
                        dest="zip_r", help=helpmsg)

    helpmsg = "merge the IRIS waveforms in the specified folder, " + \
                "syntax: --iris_merge address_of_the_target_folder. " + \
                "[Default: 'N']"
    parser.add_option("--iris_merge", action="store",
                        dest="iris_merge", help=helpmsg)

    helpmsg = "merge the ArcLink waveforms in the specified folder, " + \
                "syntax: --arc_merge address_of_the_target_folder. " + \
                "[Default: 'N']"
    parser.add_option("--arc_merge", action="store",
                        dest="arc_merge", help=helpmsg)

    helpmsg = "merge automatically after downloading the waveforms " + \
                "from IRIS. [Default: 'Y']"
    parser.add_option("--iris_merge_auto", action="store",
                        dest="iris_merge_auto", help=helpmsg)

    helpmsg = "merge automatically after downloading the waveforms " + \
                "from ArcLink. [Default: 'Y']"
    parser.add_option("--arc_merge_auto", action="store",
                        dest="arc_merge_auto", help=helpmsg)

    helpmsg = "merge all waveforms (IRIS and ArcLink) in the " + \
                "specified folder, syntax: --merge_all " + \
                "address_of_the_target_folder. [Default: 'N']"
    parser.add_option("--merge_all", action="store",
                      dest="merge_all", help=helpmsg)

    helpmsg = "do not merge automatically. This is equivalent " + \
                "to: \"--iris_merge_auto N --arc_merge_auto N\""
    parser.add_option("--merge_no", action="store_true",
                      dest="merge_no", help=helpmsg)

    helpmsg = "merge 'raw' or 'corrected' waveforms. [Default: 'raw']"
    parser.add_option("--merge_type", action="store",
                        dest="merge_type", help=helpmsg)

    helpmsg = "plot waveforms downloaded from IRIS."
    parser.add_option("--plot_iris", action="store_true",
                      dest="plot_iris", help=helpmsg)

    helpmsg = "plot waveforms downloaded from ArcLink."
    parser.add_option("--plot_arc", action="store_true",
                      dest="plot_arc", help=helpmsg)

    helpmsg = "plot all waveforms (IRIS and ArcLink). [Default: 'Y']"
    parser.add_option("--plot_all", action="store",
                      dest="plot_all", help=helpmsg)

    helpmsg = "plot 'raw' or 'corrected' waveforms. [Default: 'raw']"
    parser.add_option("--plot_type", action="store",
                        dest="plot_type", help=helpmsg)

    helpmsg = "plot all the events, stations and ray path between them " + \
                "found in the specified folder, " + \
                "syntax: --plot_ray_gmt address_of_the_target_folder. " + \
                "[Default: 'N']"
    parser.add_option("--plot_ray_gmt", action="store",
                      dest="plot_ray_gmt", help=helpmsg)

    helpmsg = "plot all the events found in the specified folder, " + \
                "syntax: --plot_ev address_of_the_target_folder. " + \
                "[Default: 'N']"
    parser.add_option("--plot_ev", action="store",
                      dest="plot_ev", help=helpmsg)

    helpmsg = "plot all the stations found in the specified folder, " + \
                "syntax: --plot_sta address_of_the_target_folder. " + \
                "[Default: 'N']"
    parser.add_option("--plot_sta", action="store",
                      dest="plot_sta", help=helpmsg)

    helpmsg = "plot both all the stations and all the events found " + \
                "in the specified folder, syntax: --plot_se " + \
                "address_of_the_target_folder. [Default: 'N']"
    parser.add_option("--plot_se", action="store",
                      dest="plot_se", help=helpmsg)

    helpmsg = "plot the ray coverage for all the station-event " + \
                "pairs found in the specified folder, syntax: " + \
                "--plot_ray address_of_the_target_folder. [Default: 'N']"
    parser.add_option("--plot_ray", action="store",
                      dest="plot_ray", help=helpmsg)

    helpmsg = "plot \"epicentral distance-time\" for all the " + \
                "waveforms found in the specified folder, " + \
                "syntax: --plot_epi address_of_the_target_folder. " + \
                "[Default: 'N']"
    parser.add_option("--plot_epi", action="store",
                      dest="plot_epi", help=helpmsg)

    helpmsg = "plot \"epicentral distance-time\" (refer to " + \
                "'--plot_epi') for all the waveforms with " + \
                "epicentral-distance >= min_epi. [Default: 0.0]"
    parser.add_option("--min_epi", action="store",
                      dest="min_epi", help=helpmsg)

    helpmsg = "plot \"epicentral distance-time\" (refer to " + \
                "'--plot_epi') for all the waveforms with " + \
                "epicentral-distance <= max_epi. [Default: 180.0]"
    parser.add_option("--max_epi", action="store",
                      dest="max_epi", help=helpmsg)

    helpmsg = "plot \"Data(MB)-Time(Sec)\" -- ATTENTION: " + \
                "\"time_iris\" and/or \"time_arc\" should exist in the " + \
                "\"info\" folder [refer to " + \
                "\"time_iris\" and \"time_arc\" options] " + \
                "[Default: 'N']"
    parser.add_option("--plot_dt", action="store",
                      dest="plot_dt", help=helpmsg)

    helpmsg = "the path where obspyDMT will store " + \
                "the plots [Default: '.' (the same directory " + \
                "as obspyDMT.py)]"
    parser.add_option("--plot_save", action="store",
                      dest="plot_save", help=helpmsg)

    helpmsg = "format of the plots saved on the local machine " + \
                "[Default: 'png']"
    parser.add_option("--plot_format", action="store",
                      dest="plot_format", help=helpmsg)

    helpmsg = "send an email to the specified email-address after " + \
                "completing the job, syntax: --email " + \
                "email_address. [Default: 'N']"
    parser.add_option("--email", action="store",
                      dest="email", help=helpmsg)

    # parse command line options
    (options, args) = parser.parse_args()

    return options, args, parser


def read_input_command(parser, **kwargs):
    """
    Create input object (dictionary) based on command-line options.
    The default values are as "input" object (below)
    [same in INPUT-default.cfg]
    """
    # Defining the default values.
    # Each of these values could be changed:
    # 1. By changing the 'INPUT.cfg' file (if you use
    # "'./obspyDMT.py --type file'")
    # 2. By defining the required command-line flag (if you use
    # "'./obspyDMT.py --type command'")
    input = {   'datapath': 'obspyDMT-data',

                'min_date': str(UTCDateTime() - 60 * 60 * 24 * 10 * 1),
                'max_date': str(UTCDateTime() - 60 * 60 * 24 * 5 * 1),

                'event_catalog': 'EMSC',
                'mag_type': 'Mw',
                'min_mag': 5.5, 'max_mag': 9.9,
                'min_depth': +10.0, 'max_depth': -6000.0,

                'get_events': 'Y',
                'interval': 3600*24,

                'req_np': 4,

                'waveform': 'Y', 'response': 'Y',
                'IRIS': 'Y', 'ArcLink': 'Y',

                'SAC': 'Y',

                'preset': 0.0, 'offset': 1800.0,

                'net': '*', 'sta': '*', 'loc': '*', 'cha': '*',

                'evlatmin': -90.0, 'evlatmax': +90.0,
                'evlonmin': -180.0, 'evlonmax': +180.0,

                'evlat': 0.0, 'evlon': 0.0,
                'evradmin': 0.0, 'evradmax': +180.0,

                'max_result': 2500,

                'lat_cba': None, 'lon_cba': None,
                'mr_cba': None, 'Mr_cba': None,

                'mlat_rbb': -100.0, 'Mlat_rbb': +100.0,
                'mlon_rbb': -200.0, 'Mlon_rbb': +200.0,

                'test': 'N',

                'iris_update': 'N', 'arc_update': 'N', 'update_all': 'N',

                'email': 'N',

                'ic_all': 'N',

                'iris_ic': 'N', 'iris_ic_auto': 'Y',
                'arc_ic': 'N', 'arc_ic_auto': 'Y',

                'ic_np': 20,

                'ic_obspy_full': 'Y',
                'pre_filt': '(0.008, 0.012, 3.0, 4.0)',
                'corr_unit': 'DIS',

                'merge_all': 'N',

                'iris_merge': 'N', 'iris_merge_auto': 'Y',
                'merge_type': 'raw',

                'arc_merge': 'N', 'arc_merge_auto': 'Y',

                'plot_all': 'Y',
                'plot_type': 'raw',

                'plot_ev': 'N', 'plot_sta': 'N', 'plot_se': 'N',
                'plot_ray': 'N', 'plot_epi': 'N', 'plot_dt': 'N',
                'plot_ray_gmt': 'N',
                'plot_save': '.', 'plot_format': 'png',

                'min_epi': 0.0, 'max_epi': 180.0,
            }

    # feed input dictionary of defaults into parser object
    parser.set_defaults(**input)

    # parse command line options
    (options, args) = parser.parse_args()
    # command line options can now be accessed via options.varname.

    # Check if keyword arguments have been passed to the main function from
    # another script and parse here:
    if kwargs:
        # assigning kwargs to entries of OptionParser object
        for arg in kwargs:
            exec("options.%s = kwargs[arg]") % arg

    if options.version:
        print '\t\t' + '*********************************'
        print '\t\t' + '*        obspyDMT version:      *'
        print '\t\t' + '*' + '\t\t' + '0.3.3' + '\t\t' + '*'
        print '\t\t' + '*********************************'
        print '\n'
        sys.exit(2)

    # Check whether it is possible to import all required modules
    if options.check:
        descrip = []
        descrip.append('obspy ver: ' + obspy.__version__)
        descrip.append('numpy ver: ' + np.__version__)
        descrip.append('scipy ver: ' + scipy.__version__)
        descrip.append('matplotlib ver: ' + matplotlib.__version__)

        print "*********************************"
        print "Check all the BASIC dependencies:"
        for i in range(0, len(descrip)):
            print descrip[i]
        print "*********************************\n"
        sys.exit(0)

    if options.tour:
        print '\n########################################'
        print 'obspyDMT Quick Tour will start in 5 sec!'
        print '########################################\n'
        time.sleep(5)
        options.datapath = './DMT-Tour-Data'
        options.min_date = '2011-03-10'
        options.max_date = '2011-03-12'
        options.min_mag = '8.9'
        options.identity = 'TA.1*.*.BHZ'
        options.event_catalog = 'IRIS'
        options.req_parallel = True
        options.ArcLink = 'N'

    # parse datapath (check if given absolute or relative)
    if options.datapath:
        if not os.path.isabs(options.datapath):
            options.datapath = os.path.join(os.getcwd(), options.datapath)

    if options.iris_update != 'N':
        if not os.path.isabs(options.iris_update):
            options.iris_update = os.path.join(os.getcwd(), options.iris_update)

    if options.arc_update != 'N':
        if not os.path.isabs(options.arc_update):
            options.arc_update = os.path.join(os.getcwd(), options.arc_update)

    if options.update_all != 'N':
        if not os.path.isabs(options.update_all):
            options.update_all = os.path.join(os.getcwd(), options.update_all)

    if options.iris_ic != 'N':
        if not os.path.isabs(options.iris_ic):
            options.iris_ic = os.path.join(os.getcwd(), options.iris_ic)

    if options.arc_ic != 'N':
        if not os.path.isabs(options.arc_ic):
            options.arc_ic = os.path.join(os.getcwd(), options.arc_ic)

    if options.ic_all != 'N':
        if not os.path.isabs(options.ic_all):
            options.ic_all = os.path.join(os.getcwd(), options.ic_all)

    if options.iris_merge != 'N':
        if not os.path.isabs(options.iris_merge):
            options.iris_merge = os.path.join(os.getcwd(), options.iris_merge)

    if options.arc_merge != 'N':
        if not os.path.isabs(options.arc_merge):
            options.arc_merge = os.path.join(os.getcwd(), options.arc_merge)

    if options.merge_all != 'N':
        if not os.path.isabs(options.merge_all):
            options.merge_all = os.path.join(os.getcwd(), options.merge_all)

    if options.plot_ev != 'N':
        if not os.path.isabs(options.plot_ev):
            options.plot_ev = os.path.join(os.getcwd(), options.plot_ev)

    if options.plot_sta != 'N':
        if not os.path.isabs(options.plot_sta):
            options.plot_sta = os.path.join(os.getcwd(), options.plot_sta)

    if options.plot_se != 'N':
        if not os.path.isabs(options.plot_se):
            options.plot_se = os.path.join(os.getcwd(), options.plot_se)

    if options.plot_ray != 'N':
        if not os.path.isabs(options.plot_ray):
            options.plot_ray = os.path.join(os.getcwd(), options.plot_ray)

    if options.plot_ray_gmt != 'N':
        if not os.path.isabs(options.plot_ray_gmt):
            options.plot_ray_gmt = os.path.join(os.getcwd(),
                options.plot_ray_gmt)

    if options.plot_epi != 'N':
        if not os.path.isabs(options.plot_epi):
            options.plot_epi = os.path.join(os.getcwd(), options.plot_epi)

    if options.plot_dt != 'N':
        if not os.path.isabs(options.plot_dt):
            options.plot_dt = os.path.join(os.getcwd(), options.plot_dt)

    if options.plot_save != 'N':
        if not os.path.isabs(options.plot_save):
            options.plot_save = os.path.join(os.getcwd(), options.plot_save)

    # extract min. and max. longitude and latitude if the user has given the
    # coordinates with -r (GMT syntax)
    if options.event_rect:
        try:
            options.event_rect = options.event_rect.split('/')
            if len(options.event_rect) != 4:
                print "Erroneous rectangle given."
                sys.exit(2)
            options.evlonmin = float(options.event_rect[0])
            options.evlonmax = float(options.event_rect[1])
            options.evlatmin = float(options.event_rect[2])
            options.evlatmax = float(options.event_rect[3])
        except:
            print "Erroneous rectangle given."
            sys.exit(2)

    # circular event restriction option parsing
    if options.event_circle:
        try:
            options.event_circle = options.event_circle.split('/')
            if len(options.event_circle) != 4:
                print "Erroneous circle given."
                sys.exit(2)
            options.evlon = float(options.event_circle[0])
            options.evlat = float(options.event_circle[1])
            options.evradmin = float(options.event_circle[2])
            options.evradmax = float(options.event_circle[3])
        except:
            print "Erroneous circle given."
            sys.exit(2)

    # extract min. and max. longitude and latitude if the user has given the
    # coordinates with -g (GMT syntax)
    if options.station_rect:
        try:
            options.station_rect = options.station_rect.split('/')
            if len(options.station_rect) != 4:
                print "Erroneous rectangle given."
                sys.exit(2)
            options.mlon_rbb = float(options.station_rect[0])
            options.Mlon_rbb = float(options.station_rect[1])
            options.mlat_rbb = float(options.station_rect[2])
            options.Mlat_rbb = float(options.station_rect[3])
        except:
            print "Erroneous rectangle given."
            sys.exit(2)

    # circular station restriction option parsing
    if options.station_circle:
        try:
            options.station_circle = options.station_circle.split('/')
            if len(options.station_circle) != 4:
                print "Erroneous circle given."
                sys.exit(2)
            options.lon_cba = float(options.station_circle[0])
            options.lat_cba = float(options.station_circle[1])
            options.mr_cba = float(options.station_circle[2])
            options.Mr_cba = float(options.station_circle[3])
        except:
            print "Erroneous circle given."
            sys.exit(2)

    # delete data path if -R or --reset args are given at cmdline
    if options.reset:
        # try-except so we don't get an exception if path doesnt exist
        try:
            shutil.rmtree(options.datapath)
            print '----------------------------------'
            print 'The following folder has been deleted:'
            print str(options.datapath)
            print 'obspyDMT is going to create a new folder...'
            print '----------------------------------'
        except:
            pass

    # Extract network, station, location, channel if the user has given an
    # identity code (-i xx.xx.xx.xx)
    if options.identity:
        try:
            options.net, options.sta, options.loc, options.cha = \
                                    options.identity.split('.')
        except:
            print "Erroneous identity code given."
            sys.exit(2)

    input['datapath'] = options.datapath

    input['min_date'] = str(UTCDateTime(options.min_date))
    input['max_date'] = str(UTCDateTime(options.max_date))

    input['event_catalog'] = options.event_catalog.upper()
    input['mag_type'] = options.mag_type
    input['min_mag'] = float(options.min_mag)
    input['max_mag'] = float(options.max_mag)
    input['min_depth'] = float(options.min_depth)
    input['max_depth'] = float(options.max_depth)

    input['evlonmin'] = options.evlonmin
    input['evlonmax'] = options.evlonmax
    input['evlatmin'] = options.evlatmin
    input['evlatmax'] = options.evlatmax

    input['evlat'] = options.evlat
    input['evlon'] = options.evlon
    input['evradmax'] = options.evradmax
    input['evradmin'] = options.evradmin

    input['preset'] = float(options.preset)
    input['offset'] = float(options.offset)
    input['max_result'] = int(options.max_result)

    if options.seismicity:
        input['seismicity'] = 'Y'
    else:
        input['seismicity'] = 'N'

    input['get_events'] = options.get_events

    if options.get_continuous:
        input['get_events'] = 'N'
        input['get_continuous'] = 'Y'
    else:
        input['get_continuous'] = 'N'
    input['interval'] = float(options.interval)

    if options.req_parallel:
        options.req_parallel = 'Y'
    input['req_parallel'] = options.req_parallel

    input['req_np'] = int(options.req_np)

    if options.iris_bulk:
        options.iris_bulk = 'Y'
    input['iris_bulk'] = options.iris_bulk

    input['waveform'] = options.waveform
    input['response'] = options.response
    if options.paz:
        options.paz = 'Y'
    input['paz'] = options.paz

    input['SAC'] = options.SAC
    if options.mseed: input['SAC'] = 'N'

    input['IRIS'] = options.IRIS
    input['ArcLink'] = options.ArcLink
    if options.NERIES:
        options.NERIES = 'Y'
    input['NERIES'] = options.NERIES

    if options.time_iris:
        options.time_iris = 'Y'
    input['time_iris'] = options.time_iris
    if options.time_arc:
        options.time_arc = 'Y'
    input['time_arc'] = options.time_arc

    input['net'] = options.net
    input['sta'] = options.sta
    if options.loc == "''":
        input['loc'] = ''
    elif options.loc == '""':
        input['loc'] = ''
    else:
        input['loc'] = options.loc

    input['cha'] = options.cha

    input['lon_cba'] = options.lon_cba
    input['lat_cba'] = options.lat_cba
    input['mr_cba'] = options.mr_cba
    input['Mr_cba'] = options.Mr_cba

    input['mlon_rbb'] = options.mlon_rbb
    input['Mlon_rbb'] = options.Mlon_rbb
    input['mlat_rbb'] = options.mlat_rbb
    input['Mlat_rbb'] = options.Mlat_rbb

    if options.test != 'N':
        input['test'] = 'Y'
        input['test_num'] = int(options.test)

    input['iris_update'] = options.iris_update
    input['arc_update'] = options.arc_update
    input['update_all'] = options.update_all

    if input['update_all'] != 'N':
        input['iris_update'] = input['update_all']
        input['arc_update'] = input['update_all']

    input['iris_ic'] = options.iris_ic
    input['iris_ic_auto'] = options.iris_ic_auto

    input['arc_ic'] = options.arc_ic
    input['arc_ic_auto'] = options.arc_ic_auto

    input['ic_all'] = options.ic_all

    if input['ic_all'] != 'N':
        input['iris_ic'] = input['ic_all']
        input['arc_ic'] = input['ic_all']

    if options.ic_parallel:
        options.ic_parallel = 'Y'
    input['ic_parallel'] = options.ic_parallel

    input['ic_np'] = int(options.ic_np)

    input['ic_obspy_full'] = options.ic_obspy_full

    if options.ic_sac_full:
        options.ic_sac_full = 'Y'
    input['ic_sac_full'] = options.ic_sac_full

    if options.ic_paz:
        options.ic_paz = 'Y'
    input['ic_paz'] = options.ic_paz

    if input['ic_sac_full'] == 'Y' or input['ic_paz'] == 'Y':
        input['SAC'] = 'Y'
        input['ic_obspy_full'] = 'N'

    input['corr_unit'] = options.corr_unit
    input['pre_filt'] = options.pre_filt
    if options.zip_w:
        options.zip_w = 'Y'
    input['zip_w'] = options.zip_w
    if options.zip_r:
        options.zip_r = 'Y'
    input['zip_r'] = options.zip_r

    input['iris_merge'] = options.iris_merge
    input['arc_merge'] = options.arc_merge
    input['merge_all'] = options.merge_all

    if input['merge_all'] != 'N':
        input['iris_merge'] = input['merge_all']
        input['arc_merge'] = input['merge_all']

    input['plot_type'] = options.plot_type

    input['plot_all'] = options.plot_all
    if options.plot_iris: options.plot_iris = 'Y'
    input['plot_iris'] = options.plot_iris
    if options.plot_arc: options.plot_arc = 'Y'
    input['plot_arc'] = options.plot_arc

    input['plot_ev'] = options.plot_ev
    input['plot_sta'] = options.plot_sta
    input['plot_se'] = options.plot_se
    input['plot_ray'] = options.plot_ray
    input['plot_ray_gmt'] = options.plot_ray_gmt
    input['plot_epi'] = options.plot_epi
    input['plot_dt'] = options.plot_dt

    input['min_epi'] = float(options.min_epi)
    input['max_epi'] = float(options.max_epi)

    input['plot_save'] = options.plot_save
    input['plot_format'] = options.plot_format

    input['email'] = options.email

    #--------------------------------------------------------
    if input['get_continuous'] == 'N':
        input['iris_merge_auto'] = 'N'
        input['arc_merge_auto'] = 'N'
    else:
        input['iris_merge_auto'] = options.iris_merge_auto
        input['arc_merge_auto'] = options.arc_merge_auto
        input['merge_type'] = options.merge_type

    for i in ['iris_update', 'arc_update', 'iris_ic', 'arc_ic', \
                'iris_merge', 'arc_merge', 'plot_se', 'plot_sta', \
                'plot_ev', 'plot_ray', 'plot_ray_gmt', 'plot_epi', \
                'plot_dt']:
        if input[i] != 'N':
            input['datapath'] = input[i]
            input['get_events'] = 'N'
            input['get_continuous'] = 'N'
            input['IRIS'] = 'N'
            input['ArcLink'] = 'N'
            input['iris_ic_auto'] = 'N'
            input['arc_ic_auto'] = 'N'
            input['iris_merge_auto'] = 'N'
            input['arc_merge_auto'] = 'N'

    if options.IRIS == 'N':
        input['iris_ic_auto'] = 'N'
        input['iris_merge_auto'] = 'N'
    if options.ArcLink == 'N':
        input['arc_ic_auto'] = 'N'
        input['arc_merge_auto'] = 'N'

    if options.ic_no:
        input['iris_ic_auto'] = 'N'
        input['arc_ic_auto'] = 'N'

    if options.merge_no:
        input['iris_merge_auto'] = 'N'
        input['arc_merge_auto'] = 'N'

    if input['plot_iris'] == 'Y' or input['plot_arc'] == 'Y':
        input['plot_all'] = 'N'

    if options.event_info:
        input['IRIS'] = 'N'
        input['ArcLink'] = 'N'
        input['iris_ic_auto'] = 'N'
        input['arc_ic_auto'] = 'N'
        input['iris_merge_auto'] = 'N'
        input['arc_merge_auto'] = 'N'

    if options.seismicity:
        input['IRIS'] = 'N'
        input['ArcLink'] = 'N'
        input['iris_ic_auto'] = 'N'
        input['arc_ic_auto'] = 'N'
        input['iris_merge_auto'] = 'N'
        input['arc_merge_auto'] = 'N'
        input['max_result'] = 1000000


###################### get_Events ######################################

def get_Events(input, request):

    """
    Getting list of events from NERIES

    NERIES: a client for the Seismic Data Portal (http://www.seismicportal.eu)
    which was developed under the European Commission-funded NERIES project.

    The Portal provides a single point of access to diverse,
    distributed European earthquake data provided in a unique joint
    initiative by observatories and research institutes in and around Europe.
    """

    t_event_1 = datetime.now()

    global events

    Period = input['min_date'].split('T')[0] + '_' + \
        input['max_date'].split('T')[0] + '_' + \
        str(input['min_mag']) + '_' + str(input['max_mag'])
    eventpath = os.path.join(input['datapath'], Period)

    if os.path.exists(eventpath) == True:
        print '--------------------------------------------------------'

        if raw_input('Folder for requested Period:' + '\n' + \
            str(eventpath) + \
            '\n' + 'exists in your directory.' + '\n\n' + \
            'You could either:' + '\n' + 'N: Close the program and try the ' + \
            'updating mode.' + '\n' + \
            'Y: Remove the tree, continue the program ' + \
            'and download again.' + \
            '\n\n' + 'Do you want to continue? (Y/N)' + '\n').upper() == 'Y':
            print '--------------------------------------------------------'
            shutil.rmtree(eventpath)
            os.makedirs(eventpath)

        else:
            print '--------------------------------------------------------'
            print 'So...you decided to update your folder...Ciao'
            print '--------------------------------------------------------'
            sys.exit()

    else:
        os.makedirs(eventpath)

    events = events_info(request)

    os.makedirs(os.path.join(eventpath, 'EVENT'))
    len_events = len(events)

    print 'Length of the events found based on the inputs: ' + \
            str(len_events) + '\n'

    for i in range(0, len_events):
        print "Event No:" + " " + str(i+1)
        print "Date Time:" + " " + str(events[i]['datetime'])
        print "Depth:" + " " + str(events[i]['depth'])
        print "Event-ID:" + " " + events[i]['event_id']
        try:
            print "Flynn-Region:" + " " + events[i]['flynn_region']
        except:
            print "Flynn-Region:" + " " + "NONE"
        print "Latitude:" + " " + str(events[i]['latitude'])
        print "Longitude:" + " " + str(events[i]['longitude'])
        print "Magnitude:" + " " + str(events[i]['magnitude'])
        print "-------------------------------------------------"

    Event_cat = open(os.path.join(eventpath, 'EVENT', 'EVENT-CATALOG'), 'a+')
    Event_cat.writelines(str(Period) + '\n')
    Event_cat.writelines('-------------------------------------' + '\n')
    Event_cat.writelines('Information about the requested Events:' + '\n\n')
    Event_cat.writelines('Number of Events: ' + str(len_events) + '\n')
    Event_cat.writelines('min datetime: ' + str(input['min_date']) + '\n')
    Event_cat.writelines('max datetime: ' + str(input['max_date']) + '\n')
    Event_cat.writelines('min magnitude: ' + str(input['min_mag']) + '\n')
    Event_cat.writelines('max magnitude: ' + str(input['max_mag']) + '\n')
    Event_cat.writelines('min latitude: ' + str(input['evlatmin']) + '\n')
    Event_cat.writelines('max latitude: ' + str(input['evlatmax']) + '\n')
    Event_cat.writelines('min longitude: ' + str(input['evlonmin']) + '\n')
    Event_cat.writelines('max longitude: ' + str(input['evlonmax']) + '\n')
    Event_cat.writelines('min depth: ' + str(input['min_depth']) + '\n')
    Event_cat.writelines('max depth: ' + str(input['max_depth']) + '\n')
    Event_cat.writelines('-------------------------------------' + '\n\n')
    Event_cat.close()


    for j in range(0, len_events):
        Event_cat = open(os.path.join(eventpath, 'EVENT', 'EVENT-CATALOG'), 'a')
        Event_cat.writelines("Event No: " + str(j) + '\n')
        Event_cat.writelines("Event-ID: " + str(events[j]['event_id']) + '\n')
        Event_cat.writelines("Date Time: " + str(events[j]['datetime']) + '\n')
        Event_cat.writelines("Magnitude: " + str(events[j]['magnitude']) + '\n')
        Event_cat.writelines("Depth: " + str(events[j]['depth']) + '\n')
        Event_cat.writelines("Latitude: " + str(events[j]['latitude']) + '\n')
        Event_cat.writelines("Longitude: " + str(events[j]['longitude']) + '\n')

        try:
            Event_cat.writelines("Flynn-Region: " + \
                                str(events[j]['flynn_region']) + '\n')

        except:
            Event_cat.writelines("Flynn-Region: " + 'None' + '\n')

        Event_cat.writelines('-------------------------------------' + '\n')
        Event_cat.close()

    Event_file = open(os.path.join(eventpath, 'EVENT', 'event_list'), 'a+')
    pickle.dump(events, Event_file)
    Event_file.close()

    print 'Events are saved!'

    print 'Length of events: ' + str(len_events) + '\n'

    t_event_2 = datetime.now()
    t_event = t_event_2 - t_event_1

    print 'Time for getting and saving the events:'
    print t_event

    return events

###################### events_info #####################################

def events_info(request):

    """
    Get the event(s) info for event-based or continuous requests
    """

    global input

    if request == 'event-based':

        print '\n###################################'
        print 'Start sending the event request to:'

        if input['event_catalog'] == 'EMSC':

            print 'EMSC'
            print '###################################\n'

            client_neries = Client_neries()

            events = client_neries.getEvents(min_datetime=input['min_date'], \
                max_datetime=input['max_date'], min_magnitude=input['min_mag'], \
                max_magnitude=input['max_mag'], min_latitude=input['evlatmin'], \
                max_latitude=input['evlatmax'], min_longitude=input['evlonmin'], \
                max_longitude=input['evlonmax'], min_depth = input['min_depth'], \
                max_depth=input['max_depth'], magnitude_type=input['mag_type'],
                max_results=input['max_result'])

        elif input['event_catalog'] == 'IRIS':
            try:
                print 'IRIS'
                print '###################################\n'

                client_iris = Client_iris()

                events_QML = client_iris.getEvents(\
                        minlat=input['evlatmin'],maxlat=input['evlatmax'],\
                        minlon=input['evlonmin'],maxlon=input['evlonmax'],\
                        lat=input['evlat'],lon=input['evlon'],\
                        maxradius=input['evradmax'],minradius=input['evradmin'],\
                        mindepth=-input['min_depth'],maxdepth=-input['max_depth'],\
                        starttime=input['min_date'],endtime=input['max_date'],\
                        minmag=input['min_mag'],maxmag=input['max_mag'],\
                        magtype=input['mag_type'])

                events = []
                for i in range(0, len(events_QML)):
                    event_time = events_QML.events[i].origins[0].time
                    if event_time.month < 10:
                        event_time_month = '0' + str(event_time.month)
                    else:
                        event_time_month = str(event_time.month)
                    if event_time.day < 10:
                        event_time_day = '0' + str(event_time.day)
                    else:
                        event_time_day = str(event_time.day)
                    events.append({\
                        'author': \
                            events_QML.events[i].magnitudes[0].creation_info.author, \
                        'event_id': str(event_time.year) + event_time_month + \
                                     event_time_day + '_' + str(i), \
                        'origin_id': 'NAN', \
                        'longitude': events_QML.events[i].origins[0].longitude, \
                        'latitude': events_QML.events[i].origins[0].latitude, \
                        'datetime': event_time, \
                        'depth': -events_QML.events[i].origins[0].depth, \
                        'magnitude': events_QML.events[i].magnitudes[0].mag, \
                        'magnitude_type': \
                            events_QML.events[i].magnitudes[0].magnitude_type.lower(), \
                        'flynn_region': 'NAN'})
            except Exception, e:
                print 30*'-'
                print e
                print 30*'-'
                events = []

        for i in range(0, len(events)):
            #client_iris.flinnengdahl(lat=-1.196, lon=121.33, rtype="code")
            events[i]['t1'] = events[i]['datetime'] - input['preset']
            events[i]['t2'] = events[i]['datetime'] + input['offset']

    elif request == 'continuous':

        print '\n###############################'
        print 'Start identifying the intervals'
        print '###############################\n'

        m_date = UTCDateTime(input['min_date'])
        M_date = UTCDateTime(input['max_date'])

        t_cont = M_date - m_date

        events = []

        if t_cont > input['interval']:
            num_div = int(t_cont/input['interval'])

            for i in range(0, num_div):
                events.append({'author': 'NAN', 'event_id': 'continuous' + str(i), \
                            'origin_id': -12345.0, 'longitude': -12345.0, \
                            'datetime': m_date + i*input['interval'], \
                            't1': m_date + i*input['interval'],\
                            't2': m_date + (i+1)*input['interval'] + 60.0,\
                            'depth': -12345.0, 'magnitude': -12345.0, \
                            'magnitude_type': 'NAN', 'latitude': -12345.0, \
                            'flynn_region': 'NAN'})

            events.append({'author': 'NAN', 'event_id': 'continuous' + str(i+1), \
                            'origin_id': -12345.0, 'longitude': -12345.0, \
                            'datetime': m_date + (i+1)*input['interval'], \
                            't1': m_date + (i+1)*input['interval'],\
                            't2': M_date,\
                            'depth': -12345.0, 'magnitude': -12345.0, \
                            'magnitude_type': 'NAN', 'latitude': -12345.0, \
                            'flynn_region': 'NAN'})
        else:
            events.append({'author': 'NAN', 'event_id': 'continuous0', \
                            'origin_id': -12345.0, 'longitude': -12345.0, \
                            'datetime': m_date, \
                            't1': m_date,\
                            't2': M_date,\
                            'depth': -12345.0, 'magnitude': -12345.0, \
                            'magnitude_type': 'NAN', 'latitude': -12345.0, \
                            'flynn_region': 'NAN'})

    return events

###################### seismicity ######################################


def IRIS_network(input):
    """
    Returns information about what time series data is available
    at the IRIS DMC for all requested events
    """
    global events

    len_events = len(events)
    Period = input['min_date'].split('T')[0] + '_' + \
                input['max_date'].split('T')[0] + '_' + \
                str(input['min_mag']) + '_' + str(input['max_mag'])
    eventpath = os.path.join(input['datapath'], Period)

    create_folders_files(events, eventpath)

    print 'IRIS-Folders are Created!'
    print "-------------------------"

    for i in range(0, len_events):

        t_iris_1 = datetime.now()

        target_path = os.path.join(eventpath, events[i]['event_id'])
        Stas_iris = IRIS_available(input, events[i], target_path,
            event_number=i)

        if input['iris_bulk'] != 'Y':
            print "\n-------------------------"
            print 'IRIS-Availability for event: ' + str(i + 1) + str('/') + \
                                    str(len_events) + '  ---> ' + 'DONE'
        else:
            print "\n-------------------------"
            print 'IRIS-bulkfile for event: ' + str(i + 1) + str('/') + \
                                    str(len_events) + '  ---> ' + 'DONE'

        t_iris_2 = datetime.now()
        t_iris = t_iris_2 - t_iris_1

        print "................."
        print 'Time:'
        print t_iris
        print "-------------------------"

        if Stas_iris:
            IRIS_waveform(input, Stas_iris, i, type='save')
        else:
            'No available station in IRIS for your request!'
            continue


def IRIS_available(input, event, target_path, event_number):
    """
    Check the availablity of the IRIS stations
    """
    client_iris = Client_iris()
    Sta_iris = []

    try:

        available = client_iris.availability(network=input['net'], \
            station=input['sta'], location=input['loc'], \
            channel=input['cha'], \
            starttime=UTCDateTime(event['t1']), \
            endtime=UTCDateTime(event['t2']), \
            lat=input['lat_cba'], \
            lon=input['lon_cba'], minradius=input['mr_cba'], \
            maxradius=input['Mr_cba'], minlat=input['mlat_rbb'], \
            maxlat=input['Mlat_rbb'], minlon=input['mlon_rbb'], \
            maxlon=input['Mlon_rbb'], output='xml')

        Sta_iris = XML_list_avail(xmlfile=available)

        if input['iris_bulk'] == 'Y':
            filename = "bulkdata-%i.txt" % event_number
            filepath = os.path.join(target_path, 'info', filename)
            if os.path.exists(filepath):
                print("%s exists in directory!" % filename)
                print(68 * "-")
            else:
                client_iris.availability(network=input['net'],
                    station=input['sta'], location=input['loc'],
                    channel=input['cha'], starttime=UTCDateTime(event['t1']),
                    endtime=UTCDateTime(event['t2']), lat=input['lat_cba'],
                    lon=input['lon_cba'], minradius=input['mr_cba'],
                    maxradius=input['Mr_cba'], minlat=input['mlat_rbb'],
                    maxlat=input['Mlat_rbb'], minlon=input['mlon_rbb'],
                    maxlon=input['Mlon_rbb'], filename=filepath, output='bulk')

    except Exception as e:
        ee = 'iris -- Event: %i---%s\n' % (event_number, str(e))
        filepath = os.path.join(target_path, 'info', 'exception')
        with open(filepath, 'a+') as open_file:
            open_file.writelines(ee)
        print e

    if not Sta_iris:
        Sta_iris.append([])

    return Sta_iris


def IRIS_waveform(input, Sta_req, i, type):
    """
    Gets Waveforms, Response files and meta-data from IRIS DMC based on the
    requested events...
    """
    t_wave_1 = datetime.now()

    global events

    client_iris = Client_iris()
    add_event = []

    if type == 'save':
        Period = input['min_date'].split('T')[0] + '_' + \
                    input['max_date'].split('T')[0] + '_' + \
                    str(input['min_mag']) + '_' + str(input['max_mag'])
        eventpath = os.path.join(input['datapath'], Period)
        for event in events:
            add_event.append(os.path.join(eventpath, event['event_id']))
    elif type == 'update':
        events, add_event = quake_info(input['iris_update'], target='info')

    if input['test'] == 'Y':
        len_req_iris = input['test_num']
    else:
        len_req_iris = len(Sta_req)

    if input['iris_bulk'] == 'Y':

        t11 = datetime.now()

        bulk_file = os.path.join(add_event[i], 'info', \
                            'bulkdata-' + str(i) + '.txt')

        print 'bulkdataselect request is sent for event: ' + \
                                    str(i + 1) + '/' + str(len(events))
        bulk_st = client_iris.bulkdataselect(bulk_file)

        print '--------'
        print 'Saving the stations...'
        print '--------'

        for bulk in bulk_st:
            bulk_st_info = bulk.stats
            bulk[m].write(os.path.join(add_event[i], 'BH_RAW', \
                bulk_st_info['network'] + '.' + \
                bulk_st_info['station'] + '.' + \
                bulk_st_info['location'] + '.' + \
                bulk_st_info['channel']), 'MSEED')

        input['waveform'] = 'N'

        t22 = datetime.now()

        print 'bulkdataselect request is done for event: ' + \
                                    str(i + 1) + '/' + str(len(events))
        print "Time: \n" + str(t22 - t11)
        print '-------------------------\n'

    dic = {}

    if input['req_parallel'] == 'Y':

        print "###################"
        print "Parallel Request"
        print "Number of Nodes: " + str(input['req_np'])
        print "###################"

        parallel_results = pprocess.Map(limit=input['req_np'], reuse=1)
        parallel_job = parallel_results.manage(
            pprocess.MakeReusable(IRIS_download_core))

        for j in range(0, len_req_iris):
            parallel_job(i=i, j=j, dic=dic, type=type, len_events=len(events),
                events=events, add_event=add_event, Sta_req=Sta_req,
                input=input)

        parallel_results.finish()

    else:
        for j in xrange(len_req_iris):
            IRIS_download_core(i=i, j=j, dic=dic, type=type,
                len_events=len(events), events=events, add_event=add_event,
                Sta_req=Sta_req, input=input)

    if input['SAC'] == 'Y':
        print '\n Converting the MSEED files to SAC...',
        writesac_all(i=i, events=events, address_events=add_event)
        print 'DONE\n'

    if input['iris_bulk'] == 'Y':
        if input['SAC'] == 'Y':
            for j in xrange(len_req_iris):
                try:
                    writesac(address_st=os.path.join(add_event[i], 'BH_RAW',
                        Sta_req[j][0] + '.' + Sta_req[j][1] + '.' +
                        Sta_req[j][2] + '.' + Sta_req[j][3]),
                        sta_info=dic[j], ev_info=events[i])
                except:
                    pass
        input['waveform'] = 'Y'

    Report = open(os.path.join(add_event[i], 'info', 'report_st'), 'a')
    eventsID = events[i]['event_id']
    Report.writelines('<><><><><><><><><><><><><><><><><>' + '\n')
    Report.writelines(eventsID + '\n')
    Report.writelines('---------------IRIS---------------' + '\n')
    Report.writelines('---------------' + input['cha'] + '---------------' +
        '\n')
    rep = 'IRIS-Available stations for channel ' + input['cha'] + \
            ' and for event' + '-' + str(i) + ': ' + str(len(Sta_req)) + '\n'
    Report.writelines(rep)
    rep = 'IRIS-' + type + ' stations for channel ' + input['cha'] + \
            ' and for event' + '-' + str(i) + ':     ' + str(len(dic)) + '\n'
    Report.writelines(rep)
    Report.writelines('----------------------------------' + '\n')

    t_wave_2 = datetime.now()
    t_wave = t_wave_2 - t_wave_1

    rep = "Time for " + type + "ing Waveforms from IRIS: " + str(t_wave) + '\n'
    Report.writelines(rep)
    Report.writelines('----------------------------------' + '\n')
    Report.close()

    if input['req_parallel'] == 'Y':
        report_parallel_open = open(os.path.join(add_event[i], \
                                    'info', 'report_parallel'), 'a')
        report_parallel_open.writelines(\
            '---------------IRIS---------------' + '\n')
        report_parallel_open.writelines(\
            'Request' + '\n')
        report_parallel_open.writelines(\
            'Number of Nodes: ' + str(input['req_np']) + '\n')

        size = get_folder_size(os.path.join(add_event[i]))
        report_parallel_open.writelines(\
            'Total Time     : ' + str(t_wave) + '\n')

        time_report = "{seconds:i},{microseconds:i},{megabyte:i},+,\n".format(
            seconds=t_wave.seconds,  microseconds=t_wave.microsecond,
            megabyte=(size / 1024 ** 2))
        report_parallel_open.writelines(time_report)

        report_parallel_open.close()

    print "\n------------------------"
    print 'IRIS for event-%i is Done' % (i + 1)
    print 'Time:'
    print t_wave
    print "------------------------\n"


def ARC_network(input):
    """
    Returns information about what time series data is available
    at the ArcLink nodes for all requested events
    """
    global events

    Period = input['min_date'].split('T')[0] + '_' + \
                input['max_date'].split('T')[0] + '_' + \
                str(input['min_mag']) + '_' + str(input['max_mag'])
    eventpath = os.path.join(input['datapath'], Period)

    if input['IRIS'] != 'Y':
        create_folders_files(events, eventpath)

    print 'ArcLink-Folders are Created!'
    print "----------------------------"

    for i, event in enumerate(events):
        t_arc_1 = datetime.now()
        Stas_arc = ARC_available(input, event, eventpath, event_number=i)

        print "\n-------------------------"
        print 'ArcLink-Availability for event: ' + str(i + 1) + str('/') + \
                                    str(len(events)) + '  --->' + 'DONE'

        t_arc_2 = datetime.now()
        t_arc_21 = t_arc_2 - t_arc_1

        print "................."
        print 'Time:'
        print t_arc_21
        print "-------------------------"

        if Stas_arc:
            ARC_waveform(events, input, Stas_arc, i, type='save')
        else:
            'No available station in ArcLink for your request!'


def ARC_available(input, event, target_path, event_number):

    """
    Check the availablity of the ArcLink stations
    """

    client_arclink = Client_arclink()
    Sta_arc = []

    try:

        inventories = client_arclink.getInventory(network=input['net'],
            station=input['sta'], location=input['loc'],
            channel=input['cha'],
            starttime=UTCDateTime(event['datetime']) - 10,
            endtime=UTCDateTime(event['datetime']) + 10,
            instruments=False, route=True, sensortype='',
            min_latitude=None, max_latitude=None,
            min_longitude=None, max_longitude=None,
            restricted=False, permanent=None, modified_after=None)

        for j in inventories.keys():
            netsta = j.split('.')
            if len(netsta) == 4:
                sta = netsta[0] + '.' + netsta[1]
                if inventories[sta]['depth'] == None:
                    inventories[sta]['depth'] = 0.0
                if input['mlat_rbb'] <= inventories[sta]['latitude'] <= \
                        input['Mlat_rbb'] and \
                    input['mlon_rbb'] <= inventories[sta]['longitude'] <= \
                        input['Mlon_rbb']:
                    Sta_arc.append([netsta[0], netsta[1], netsta[2], netsta[3],
                        inventories[sta]['latitude'],
                        inventories[sta]['longitude'],
                        inventories[sta]['elevation'],
                        inventories[sta]['depth']])

        if len(Sta_arc) == 0:
            Sta_arc.append([])

        Sta_arc.sort()

    except Exception, e:

        Exception_file = open(os.path.join(target_path, \
            'info', 'exception'), 'a+')
        ee = 'arclink -- Event:' + str(event_number) + '---' + str(e) + '\n'

        Exception_file.writelines(ee)
        Exception_file.close()
        print e

    return Sta_arc


def IRIS_update(input, address):
    """
    Initialize folders and required stations for IRIS update requests
    """
    t_update_1 = datetime.now()

    client_iris = Client_iris()

    events, address_events = quake_info(address, 'info')
    len_events = len(events)

    for i in range(len_events):
        target_path = address_events
        Stas_iris = IRIS_available(input, events[i], target_path[i],
                event_number=i)

        if input['iris_bulk'] != 'Y':
            print 'IRIS-Availability for event: ' + str(i + 1) + str('/') + \
                                    str(len_events) + '  ---> ' + 'DONE'
        else:
            print 'IRIS-bulkfile for event    : ' + str(i + 1) + str('/') + \
                                    str(len_events) + '  ---> ' + 'DONE'

        if Stas_iris != [[]]:
            Stas_req = rm_duplicate(Stas_iris,
                            address=os.path.join(address_events[i]))
        else:
            Stas_req = [[]]
            print '------------------------------------------'
            print 'There is no available station!'
            print '------------------------------------------'
        if not os.path.isdir(os.path.join(address_events[i], 'BH_RAW')):
            os.makedirs(os.path.join(address_events[i], 'BH_RAW'))

        if Stas_req:
            IRIS_waveform(input, Stas_req, i, type='update')
        else:
            'No available station in IRIS for your request!'
            continue


def ARC_update(input, address):
    """
    Initialize folders and required stations for ARC update requests
    """
    t_update_1 = datetime.now()

    client_arclink = Client_arclink()

    events, address_events = quake_info(address, 'info')
    len_events = len(events)

    for i in range(len_events):
        target_path = address_events
        Stas_arc = ARC_available(input, events[i], target_path[i],
            event_number=i)

        print 'ArcLink-Availability for event: ' + str(i + 1) + str('/') + \
                                    str(len_events) + '  --->' + 'DONE'

        if Stas_arc != [[]]:
            Stas_req = rm_duplicate(Stas_arc, \
                            address=os.path.join(address_events[i]))
        else:
            Stas_req = [[]]
            print '------------------------------------------'
            print 'There is no available station!'
            print '------------------------------------------'
        if not os.path.isdir(os.path.join(address_events[i], 'BH_RAW')):
            os.makedirs(os.path.join(address_events[i], 'BH_RAW'))

        if Stas_req:
            ARC_waveform(events, input, Stas_req, i, type='update')
        else:
            'No available station in ArcLink for your request!'
            continue


def IRIS_ARC_IC(input, clients):
    """
    Call "inst_correct" function based on the channel request.
    """
    if input[clients + '_ic_auto'] == 'Y':
        global events
        Period = input['min_date'].split('T')[0] + '_' + \
                    input['max_date'].split('T')[0] + '_' + \
                    str(input['min_mag']) + '_' + str(input['max_mag'])
        eventpath = os.path.join(input['datapath'], Period)
        address = eventpath
    elif input[clients + '_ic'] != 'N':
        address = input[clients + '_ic']

    events, address_events = quake_info(address, 'info')

    for i in range(0, len(events)):
        sta_ev = read_station_event(address_events[i])
        ls_saved_stas_tmp = []
        ls_saved_stas = []

        for j in range(0, len(sta_ev[0])):
            if clients == sta_ev[0][j][13]:
                station_id = sta_ev[0][j][0] + '.' + sta_ev[0][j][1] + '.' + \
                             sta_ev[0][j][2] + '.' + sta_ev[0][j][3]
                ls_saved_stas_tmp.append(os.path.join(address_events[i],
                    'BH_RAW', station_id))

        pattern_sta = input['net'] + '.' + input['sta'] + '.' + \
                        input['loc'] + '.' + input['cha']

        for k in range(0, len(ls_saved_stas_tmp)):
            if fnmatch.fnmatch(ls_saved_stas_tmp[k].split('/')[-1],
                pattern_sta):
                ls_saved_stas.append(ls_saved_stas_tmp[k])

        if len(ls_saved_stas) != 0:
            print '\n=================='
            print 'event: ' + str(i + 1) + '/' + str(len(events)) + \
                                                            ' -- ' + clients
            print '=================='
            inst_correct(input, ls_saved_stas, address_events[i], clients)
        else:
            print "There is no station in the folder to correct!"

    print "**********************************"
    print clients.upper() + ' Instrument Correction is DONE'
    print "**********************************"


def inst_correct(input, ls_saved_stas, address, clients):
    """
    Apply Instrument Coorection on all available stations in the folder
    This scrips uses 'seisSim' from obspy.signal for this reason

    Instrument Correction has three main steps:
        1) RTR: remove the trend
        2) tapering
        3) pre-filtering and deconvolution of Resp file from Raw counts

    Remove the instrument type by deconvolution using spectral division.
    """
    t_inst_1 = datetime.now()

    if input['corr_unit'] == 'DIS':
        BH_file = 'BH'
    else:
        BH_file = 'BH_' + input['corr_unit']

    try:
        os.makedirs(os.path.join(address, BH_file))
    except Exception as e:
        pass

    if input['ic_parallel'] == 'Y':
        print "##############################"
        print "Parallel Instrument Correction"
        print "Number of Nodes: " + str(input['ic_np'])
        print "##############################"

        parallel_results = pprocess.Map(limit=input['ic_np'], reuse=1)
        parallel_job = parallel_results.manage(pprocess.MakeReusable(IC_core))

        for i in range(0, len(ls_saved_stas)):
            parallel_job(ls_saved_stas=ls_saved_stas[i], clients=clients,
                address=address, BH_file=BH_file,
                inform=clients + ' -- ' + str(i + 1) + '/' +
                str(len(ls_saved_stas)))

        parallel_results.finish()

    else:
        for i in range(0, len(ls_saved_stas)):
            IC_core(ls_saved_stas=ls_saved_stas[i], clients=clients,
                address=address, BH_file=BH_file, inform=clients + ' -- ' +
                str(i + 1) + '/' + str(len(ls_saved_stas)))

    # ---------Creating Tar files (Response files)
    if input['zip_w'] == 'Y':

        print '*********************'
        print 'Compressing Raw files'
        print '*********************'

        path = os.path.join(address, 'BH_RAW')
        tar_file = os.path.join(path, 'BH_RAW.tar')
        files = '*.*.*.*'

        compress_gzip(path=path, tar_file=tar_file, files=files)

    # ---------Creating Tar files (Response files)
    if input['zip_r'] == 'Y':

        print '**************************'
        print 'Compressing Response files'
        print '**************************'

        path = os.path.join(address, 'Resp')
        tar_file = os.path.join(path, 'Resp.tar')
        files = '*.*.*.*'

        compress_gzip(path=path, tar_file=tar_file, files=files)

    t_inst_2 = datetime.now()

    if input['ic_parallel'] == 'Y':
        report_parallel_open = open(os.path.join(address, \
                                    'info', 'report_parallel'), 'a')
        report_parallel_open.writelines(\
            '---------------' + clients.upper() + '---------------' + '\n')
        report_parallel_open.writelines(\
            'Instrument Correction' + '\n')
        report_parallel_open.writelines(\
            'Number of Nodes: ' + str(input['ic_np']) + '\n')
        report_parallel_open.writelines(\
            'Number of Stas : ' + str(len(ls_saved_stas)) + '\n')
        report_parallel_open.writelines(\
            'Total Time     : ' + str(t_inst_2 - t_inst_1) + '\n')

    print '-----------------------------------------------'
    print 'Time for Instrument Correction of ' + \
                    str(len(ls_saved_stas)) + ' stations:'
    print t_inst_2 - t_inst_1
    print '-----------------------------------------------'


def IC_core(ls_saved_stas, clients, address, BH_file, inform):
    """
    XXX: Add documentation.
    """
    global input

    try:
        if input['ic_obspy_full'] == 'Y':
            # Removing the trend
            rt_c = RTR(stream=ls_saved_stas, degree=2)
            tr = read(ls_saved_stas)[0]
            tr.data = rt_c

            # Tapering
            taper = invsim.cosTaper(len(tr.data))
            tr.data *= taper

            resp_file = os.path.join(address, 'Resp', 'RESP' + '.' +
                                        ls_saved_stas.split('/')[-1])

            obspy_fullresp(trace=tr, resp_file=resp_file,
                Address=os.path.join(address, BH_file),
                unit=input['corr_unit'], BP_filter=input['pre_filt'],
                inform=inform)

        if input['ic_sac_full'] == 'Y':
            resp_file = os.path.join(address, 'Resp', 'RESP' + '.' +
                                        ls_saved_stas.split('/')[-1])

            SAC_fullresp(trace=ls_saved_stas, resp_file=resp_file,
                address=address, BH_file=BH_file, unit=input['corr_unit'],
                BP_filter=input['pre_filt'], inform=inform)

        if input['ic_paz'] == 'Y':
            if clients == 'iris':
                paz_file = os.path.join(address, 'Resp', 'PAZ' + '.' +
                                ls_saved_stas.split('/')[-1] + '.' + 'full')

                SAC_PAZ(trace=ls_saved_stas, paz_file=paz_file,
                    address=address, BH_file=BH_file, unit=input['corr_unit'],
                    BP_filter=input['pre_filt'], inform=inform)

            if clients == 'arc':
                rt_c = RTR(stream=ls_saved_stas, degree=2)
                tr = read(ls_saved_stas)[0]
                tr.data = rt_c

                # Tapering
                taper = invsim.cosTaper(len(tr.data))
                tr.data *= taper

                resp_file = os.path.join(address, 'Resp', 'RESP' + '.' +
                                            ls_saved_stas.split('/')[-1])

                obspy_PAZ(trace=tr, resp_file=resp_file,
                    Address=os.path.join(address, BH_file), clients=clients,
                    unit=input['corr_unit'], BP_filter=input['pre_filt'],
                    inform=inform)

    except Exception as e:
        print e


def RTR(stream, degree=2):
    """
    Remove the trend by Fitting a linear function to the trace
    with least squares and subtracting it

    XXX: The same functionality is included in ObsPy. Potentially replace it.
    """

    raw_f = read(stream)

    t = []
    b0 = 0
    inc = []

    b = raw_f[0].stats['starttime']

    for i in range(0, raw_f[0].stats['npts']):
        inc.append(b0)
        b0 = b0 + 1.0 / raw_f[0].stats['sampling_rate']
        b0 = round(b0, 4)

    A = np.vander(inc, degree)
    (coeffs, residuals, rank, sing_vals) = np.linalg.lstsq(A, raw_f[0].data)

    f = np.poly1d(coeffs)
    y_est = f(inc)
    rt_c = raw_f[0].data - y_est

    return rt_c


def obspy_fullresp(trace, resp_file, Address, unit='DIS',
    BP_filter=(0.008, 0.012, 3.0, 4.0), inform='N/N'):
    """
    XXX: Add documentation.
    """
    date = trace.stats['starttime']
    seedresp = {'filename': resp_file, 'date': date, 'units': unit}

    try:
        trace.data = seisSim(data=trace.data,
            samp_rate=trace.stats.sampling_rate, paz_remove=None,
            paz_simulate=None, remove_sensitivity=True,
            simulate_sensitivity=False, water_level=600.0,
            zero_mean=True, taper=False, pre_filt=eval(BP_filter),
            seedresp=seedresp, pitsasim=False, sacsim=True)

        trace_identity = trace.stats['station'] + '.' + \
                trace.stats['location'] + '.' + trace.stats['channel']
        trace.write(os.path.join(Address, unit.lower() + '.' + trace_identity),
            format='SAC')

        if unit.lower() == 'dis':
            unit_print = 'displacement'
        if unit.lower() == 'vel':
            unit_print = 'velocity'
        if unit.lower() == 'acc':
            unit_print = 'acceleration'

        print inform + ' -- Instrument Correction to ' + unit_print + \
                                            ' for: ' + trace_identity

    except Exception as e:
        print inform + ' -- ' + str(e)


def SAC_fullresp(trace, resp_file, address, BH_file='BH', unit='DIS',
                    BP_filter=(0.008, 0.012, 3.0, 4.0), inform='N/N'):
    """
    This script runs SAC program for instrument correction
    Instrument Correction will be done for all waveforms in the BH_RAW folder
    Response files will be loaded from Resp folder

    Instrument Correction has three main steps:
    1) RTR: remove the trend
    2) tapering
    3) pre-filtering and deconvolution of Resp file from Raw counts
    """
    try:

        trace_info = trace.split('/')[-1].split('.')

        if unit.lower() == 'dis':
            unit_sac = 'NONE'
        if unit.lower() == 'vel':
            unit_sac = 'VEL'
        if unit.lower() == 'acc':
            unit_sac = 'ACC'

        BP_filter_tuple = eval(BP_filter)
        freqlim = str(BP_filter_tuple[0]) + ' ' + str(BP_filter_tuple[1]) \
                    + ' ' + str(BP_filter_tuple[2]) + ' ' + \
                    str(BP_filter_tuple[3])

        pwd = commands.getoutput('pwd')
        os.chdir(os.path.join(address, BH_file))

        p = subprocess.Popen(['sac'], stdout=subprocess.PIPE,
            stdin=subprocess.PIPE, stderr=subprocess.STDOUT)

        s = \
        'setbb resp ../Resp/' + resp_file.split('/')[-1] + '\n' + \
        'read ../BH_RAW/' + trace.split('/')[-1] + '\n' + \
        'rtrend' + '\n' + \
        'taper' + '\n' + \
        'rmean' + '\n' + \
        'trans from evalresp fname %resp to ' + unit_sac + ' freqlim ' + \
        freqlim + '\n' + \
        'write ' + unit.lower() + '.' + trace_info[1] + '.' + trace_info[2] + \
                                            '.' + trace_info[3] + '\n' + \
        'quit\n'

        out = p.communicate(s)
        print out[0]
        os.chdir(pwd)

        if unit.lower() == 'dis':
            unit_print = 'displacement'
        if unit.lower() == 'vel':
            unit_print = 'velocity'
        if unit.lower() == 'acc':
            unit_print = 'acceleration'

        print inform + ' -- Instrument Correction to ' + unit_print + \
                        ' for: ' + trace_info[0] + '.' + trace_info[1] + \
                        '.' + trace_info[2] + '.' + trace_info[3]
        print "-----------------------------------"

    except Exception, e:
        print inform + ' -- ' + str(e)


def readRESP(resp_file, unit):
    """
    XXX: Add documentation.
    """
    resp_open = open(resp_file)
    resp_read = resp_open.readlines()

    check_resp = []

    for resp_line in resp_read:
        if "velocity in meters per second" in resp_line.lower() or \
            "velocity in meters/second" in resp_line.lower() or \
            "m/s -" in resp_line.lower():
            check_resp.append('M/S')

        elif "m/s**2 - acceleration" in resp_line.lower():
            check_resp.append('M/S**2')

    if not check_resp:
        print '\n*************************************************************'
        print 'The response file is not in the right dimension (M/S) or ' + \
            '(M/S**2)'
        print 'This could cause problems in the instrument correction.'
        print 'Please check the response file:'
        print resp_file
        print '***************************************************************'
        sys.exit()

    gain_num = []
    A0_num = []
    poles_num = []
    poles = []
    zeros = []
    zeros_num = []
    #if clients == 'iris':
    if resp_read[0].find('obspy.xseed') == -1:
        for i in range(0, len(resp_read)):
            if resp_read[i].find('B058F04') != -1:
                gain_num.append(i)
            if resp_read[i].find('B053F07') != -1:
                A0_num.append(i)
            if resp_read[i].find('B053F10-13') != -1:
                zeros_num.append(i)
            if resp_read[i].find('B053F15-18') != -1:
                poles_num.append(i)

    #elif clients == 'arc':
    elif resp_read[0].find('obspy.xseed') != -1:
        for i in range(0, len(resp_read)):
            if resp_read[i].find('B058F04') != -1:
                gain_num.append(i)
            if resp_read[i].find('B043F08') != -1:
                A0_num.append(i)
            if resp_read[i].find('B043F11-14') != -1:
                zeros_num.append(i)
            if resp_read[i].find('B043F16-19') != -1:
                poles_num.append(i)

    list_sensitivity = resp_read[gain_num[-1]].split('\n')[0].split(' ')
    list_new_sensitivity = [x for x in list_sensitivity if x]
    sensitivity = eval(list_new_sensitivity[-1])

    list_A0 = resp_read[A0_num[0]].split('\n')[0].split(' ')
    list_new_A0 = [x for x in list_A0 if x]
    A0 = eval(list_new_A0[-1])

    for i in range(len(poles_num)):

        list_poles = resp_read[poles_num[i]].split('\n')[0].split(' ')
        list_new_poles = [x for x in list_poles if x]

        poles_r = eval(list_new_poles[-4])
        poles_i = eval(list_new_poles[-3])
        poles.append(complex(poles_r, poles_i))

    for i in range(0, len(zeros_num)):

        list_zeros = resp_read[zeros_num[i]].split('\n')[0].split(' ')
        list_new_zeros = [x for x in list_zeros if x]

        zeros_r = eval(list_new_zeros[-4])
        zeros_i = eval(list_new_zeros[-3])
        zeros.append(complex(zeros_r, zeros_i))

    if check_resp[0] == 'M/S':
        if unit.lower() == 'dis':
            zeros.append(0j)
        #if unit.lower() == 'vel':
        #    zeros = [0j, 0j]
        #if unit.lower() == 'acc':
        #    zeros = [0j]
    elif check_resp[0] == 'M/S**2':
        if unit.lower() == 'dis':
            zeros.append(0j)
            zeros.append(0j)

    paz = {\
    'poles': poles,
    'zeros': zeros,
    'gain': A0,
    'sensitivity': sensitivity\
    }

    return paz


def obspy_PAZ(trace, resp_file, Address, clients, unit='DIS',
    BP_filter=(0.008, 0.012, 3.0, 4.0), inform='N/N'):
    """
    Add documentation.
    """
    try:
        paz = readRESP(resp_file, unit)

        trace.data = seisSim(data=trace.data,
            samp_rate=trace.stats.sampling_rate, paz_remove=paz,
            paz_simulate=None, remove_sensitivity=True,
            simulate_sensitivity=False, water_level=600.0, zero_mean=True,
            taper=False, pre_filt=eval(BP_filter), seedresp=None,
            pitsasim=False, sacsim=True)

        trace.data *= 1.e9

        trace_identity = trace.stats['station'] + '.' + \
                trace.stats['location'] + '.' + trace.stats['channel']
        trace.write(os.path.join(Address, unit.lower() + '.' + \
                                        trace_identity), format='SAC')

        if unit.lower() == 'dis':
            unit_print = 'displacement'
        if unit.lower() == 'vel':
            unit_print = 'velocity'
        if unit.lower() == 'acc':
            unit_print = 'acceleration'

        print inform + ' -- Instrument Correction to ' + unit_print + \
                                            ' for: ' + trace_identity

    except Exception, e:
        print inform + ' -- ' + str(e)


def SAC_PAZ(trace, paz_file, address, BH_file='BH', unit='DIS', \
        BP_filter=(0.008, 0.012, 3.0, 4.0), inform='N/N'):
    """
    This script runs SAC program for instrument correction (PAZ)
    Instrument Correction will be done for all waveforms in the BH_RAW folder
    PAZ files will be loaded from Resp folder

    Instrument Correction has three main steps:
    1) RTR: remove the trend
    2) tapering
    3) pre-filtering and deconvolution of PAZ from Raw counts
    """

    try:

        trace_info = trace.split('/')[-1].split('.')

        if unit.lower() == 'dis':
            unit_sac = 'NONE'
        if unit.lower() == 'vel':
            unit_sac = 'VEL'
        if unit.lower() == 'acc':
            unit_sac = 'ACC'

        BP_filter_tuple = eval(BP_filter)
        freqlim = str(BP_filter_tuple[0]) + ' ' + str(BP_filter_tuple[1]) \
            + ' ' + str(BP_filter_tuple[2]) + ' ' + str(BP_filter_tuple[3])

        pwd = commands.getoutput('pwd')
        os.chdir(os.path.join(address, BH_file))

        p = subprocess.Popen(['sac'], stdout=subprocess.PIPE,
            stdin=subprocess.PIPE, stderr=subprocess.STDOUT)

        s = \
        'setbb pzfile ../Resp/' + paz_file.split('/')[-1] + '\n' + \
        'read ../BH_RAW/' + trace.split('/')[-1] + '\n' + \
        'rtrend' + '\n' + \
        'taper' + '\n' + \
        'rmean' + '\n' + \
        'trans from polezero s %pzfile to ' + unit_sac + ' freqlim ' + \
         freqlim + '\n' + \
        'MUL 1.0e9' + '\n' + \
        'write ' + unit.lower() + '.' + trace_info[1] + '.' + trace_info[2] + \
                                            '.' + trace_info[3] + '\n' + \
        'quit\n'

        out = p.communicate(s)
        print out[0]
        os.chdir(pwd)

        if unit.lower() == 'dis':
            unit_print = 'displacement'
        if unit.lower() == 'vel':
            unit_print = 'velocity'
        if unit.lower() == 'acc':
            unit_print = 'acceleration'

        print inform + ' -- Instrument Correction to ' + unit_print + \
                        ' for: ' + trace_info[0] + '.' + trace_info[1] + \
                        '.' + trace_info[2] + '.' + trace_info[3]

    except Exception, e:
        print inform + ' -- ' + str(e)


def IRIS_ARC_merge(input, clients):
    """
    Call "merge_stream" function
    """

    if input[clients + '_merge_auto'] == 'Y':
        global events
        Period = input['min_date'].split('T')[0] + '_' + \
                    input['max_date'].split('T')[0] + '_' + \
                    str(input['min_mag']) + '_' + str(input['max_mag'])
        eventpath = os.path.join(input['datapath'], Period)
        address = eventpath
    elif input[clients + '_merge'] != 'N':
        address = input[clients + '_merge']

    events, address_events = quake_info(address, 'info')

    ls_saved_stas_tmp = []
    ls_saved_stas = []

    for i in range(0, len(events)):
        sta_ev = read_station_event(address_events[i])
        for j in range(0, len(sta_ev[0])):
            if clients == sta_ev[0][j][13]:

                if input['merge_type'] == 'raw':
                    BH_file = 'BH_RAW'
                    network = sta_ev[0][j][0]
                    network_name = 'raw'
                elif input['merge_type'] == 'corrected':
                    if input['corr_unit'] == 'DIS':
                        BH_file = 'BH'
                        network = 'dis'
                        network_name = 'dis'
                    elif input['corr_unit'] == 'VEL':
                        BH_file = 'BH_' + input['corr_unit']
                        network = 'vel'
                        network_name = 'vel'
                    elif input['corr_unit'] == 'ACC':
                        BH_file = 'BH_' + input['corr_unit']
                        network = 'acc'
                        network_name = 'acc'

                station_id = network + '.' + sta_ev[0][j][1] + '.' + \
                             sta_ev[0][j][2] + '.' + sta_ev[0][j][3]
                ls_saved_stas_tmp.append(os.path.join(address_events[i], BH_file,\
                                        station_id))

    pattern_sta = input['net'] + '.' + input['sta'] + '.' + \
                    input['loc'] + '.' + input['cha']

    for k in range(0, len(ls_saved_stas_tmp)):
        if fnmatch.fnmatch(ls_saved_stas_tmp[k].split('/')[-1], pattern_sta):
            ls_saved_stas.append(ls_saved_stas_tmp[k])

    if len(ls_saved_stas) != 0:
        ls_saved_stations = []
        ls_address = []
        for i in range(0, len(ls_saved_stas)):
            ls_saved_stations.append(ls_saved_stas[i].split('/')[-1])
        ls_sta = list(set(ls_saved_stations))
        for i in range(0, len(address_events)):
            ls_address.append(os.path.join(address_events[i], BH_file))
        print '-----------------------------'
        merge_stream(ls_address=ls_address, ls_sta=ls_sta,
            network_name=network_name)
        print 'DONE'
        print '*****************************'
    else:
        print "There is no waveform to merege! Please check your folders!"
        print '*****************************'


def merge_stream(ls_address, ls_sta, network_name):
    """
    XXX: Add documentation.
    """
    global input

    address = os.path.dirname(os.path.dirname(ls_address[0]))
    try:
        os.makedirs(os.path.join(address, 'MERGED' + '-' + network_name))
    except Exception, e:
        pass

    for i in range(0, len(ls_sta)):
        for j in range(0, len(ls_address)):
            if os.path.isfile(os.path.join(ls_address[j], ls_sta[i])):
                st = read(os.path.join(ls_address[j], ls_sta[i]))
                for k in range(j+1, len(ls_address)):
                    try:
                        st.append(read(os.path.join(ls_address[k], \
                                                        ls_sta[i]))[0])
                    except Exception, e:
                        print e

                st.merge(method=1, fill_value='latest', interpolation_samples=0)
                trace = st[0]
                trace_identity = trace.stats['network'] + '.' + \
                        trace.stats['station'] + '.' + \
                        trace.stats['location'] + '.' + trace.stats['channel']
                st.write(os.path.join(address, 'MERGED' + '-' + network_name, \
                                        trace_identity), format = 'SAC')
                break


def __main__():
    """
    XXX: Add documentation.
    """
    global t1_pro, t1_str

    t1_pro = time.time()
    t1_str = datetime.now()

    status = obspyDMT()

    try:
        global input, events
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

    except Exception as e:
        print e
        pass

    sys.exit(status)

if __name__ == "__main__":
    parse_commands()
    #__main__()
