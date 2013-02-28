#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple function using bulk waveform download services.

Queries ArcLink and the IRIS webservices.

:copyright:
    Lion Krischer (krischer@geophysik.uni-muenchen.de), 2013
:license:
    GNU General Public License, Version 3
    (http://www.gnu.org/licenses/gpl-3.0-standalone.html)
"""
from obspy import Stream
import obspy.arclink
import obspy.iris
import Queue
import threading
import time
import warnings


def download_waveforms(channels, starttime, endtime, minimumlength,
        save_trace_fct, arclink_user, logger=None):
    """
    :param save_trace_fct: Function taking a single obspy.Trace and storing it
        however the user sees fit.
    """
    failed_downloads = []
    successful_downloads = []
    minimum_duration = minimumlength * (endtime - starttime)

    # Download first from IRIS
    st = starttime.strftime("%Y-%jT%H:%M:%S")
    et = endtime.strftime("%Y-%jT%H:%M:%S")

    def to_bulkdatarequest(channels):
        for channel in channels:
            net, sta, loc, chan = channel.split(".")
            if loc == "":
                loc = "--"
            yield "%s %s %s %s %s %s" % (net, sta, loc, chan, st, et)

    bk = "\n".join(to_bulkdatarequest(channels))
    iris_client = obspy.iris.Client()
    if logger:
        logger.debug("Starting IRIS bulkdataselect download...")
    try:
        stream = iris_client.bulkdataselect(bk,
            minimumlength=(endtime - starttime) * 0.9)
    except Exception as e:
        if not e.message.lower().startswith("no waveform data available"):
            msg = "Problem downloading data from IRIS\n"
            err_msg = str(e)
            msg += "\t%s: %s" % (e.__class__.__name__, err_msg)
            if logger:
                logger.error(msg)
            else:
                warnings.warn(msg)
        else:
            if logger:
                logger.debug("No data available at IRIS for request.")
        # Dummy stream to be able to use the same logic later on.
        stream = Stream()

    for tr in stream:
        if not tr.stats.npts or (tr.stats.endtime - tr.stats.starttime) < \
                minimum_duration:
            continue
        save_trace_fct(tr)
        successful_downloads.append(tr.id)
        if logger:
            logger.info("Successfully downloaded %s from IRIS." % tr.id)

    # Now get a list of all failed downloads.
    failed_downloads = [_i for _i in channels if _i not in
        successful_downloads]

    # Attempt to download via ArcLink first.

    class ArcLinkDownloadThread(threading.Thread):
        def __init__(self, queue):
            self.queue = queue
            super(ArcLinkDownloadThread, self).__init__()

        def run(self):
            while True:
                try:
                    channel = self.queue.get(False)
                except Queue.Empty:
                    break
                time.sleep(0.5)
                if logger:
                    logger.debug("Starting ArcLink download for %s..." %
                        channel)
                arc_client = obspy.arclink.Client(user=arclink_user)
                try:
                    st = arc_client.getWaveform(*channel.split("."),
                        starttime=starttime, endtime=endtime, format="mseed")
                except Exception as e:
                    if e.message.lower() != "no data available":
                        msg = ("Failed to download %s from ArcLink because of "
                               "an error (%s: %s)") % (channel,
                               e.__class__.__name__, e.message)
                        if logger:
                            logger.error(msg)
                        else:
                            warnings.warn(msg)
                    else:
                        if logger:
                            logger.debug("No data available at ArcLink for %s."
                                % channel)
                    continue
                if len(st) != 1 or (st[0].stats.endtime -
                        st[0].stats.starttime) < minimum_duration:
                    if logger:
                        if len(st) != 1:
                            msg = "More than one Trace found."
                            logger.debug(msg)
                        else:
                            msg = ("Trace is only %.2f seconds long (%.2f "
                               "seconds required)") % (st[0].stats.endtime -
                                st[0].stats.starttime, minimum_duration)
                            logger.debug(msg)
                    continue
                save_trace_fct(st[0])
                failed_downloads.remove(channel)
                if logger:
                    logger.info("Successfully downloaded %s from ArcLink." %
                        st[0].id)

    queue = Queue.Queue()
    for channel in failed_downloads[:]:
        queue.put(channel)

    my_threads = []
    thread_count = min(10, len(failed_downloads))
    for _i in xrange(thread_count):
        thread = ArcLinkDownloadThread(queue=queue)
        my_threads.append(thread)
        thread.start()
        time.sleep(1.0)

    for thread in my_threads:
        thread.join()

    for chan in failed_downloads:
        msg = "Failed to download %s from %s to %s" % (chan, starttime,
            endtime)
        if not logger:
            warnings.warn(msg)
            continue
        logger.warning(msg)
