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
import obspy.arclink
import obspy.iris
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

    # Attempt to download via ArcLink first.
    arc_client = obspy.arclink.Client(user=arclink_user)
    for channel in channels:
        try:
            st = arc_client.getWaveform(*channel.split("."),
                starttime=starttime, endtime=endtime, format="mseed")
        except Exception as e:
            if e.message.lower() != "no data available":
                msg = ("Failed to download %s from ArcLink because of an "
                    "error (%s: %s)") % (channel, e.__class__.__name__,
                    e.message)
                if logger:
                    logger.error(msg)
                else:
                    warnings.warn(msg)
            failed_downloads.append(channel)
            continue
        if len(st) != 1 or (st[0].stats.endtime - st[0].stats.starttime) \
                < minimum_duration:
            failed_downloads.append(channel)
            continue
        save_trace_fct(st[0])
        successful_downloads.append(st[0].id)
        if logger:
            logger.info("Successfully downloaded %s from ArcLink." % st[0].id)

    # For the failed downloads, attempt again with IRIS.
    st = starttime.strftime("%Y-%jT%H:%M:%S")
    et = endtime.strftime("%Y-%jT%H:%M:%S")

    def to_bulkdatarequest(failed_downloads):
        for channel in channels:
            net, sta, loc, chan = channel.split(".")
            if loc == "":
                loc = "--"
            yield "%s %s %s %s %s %s" % (net, sta, loc, chan, st, et)

    bk = "\n".join(to_bulkdatarequest(channels))
    iris_client = obspy.iris.Client()
    try:
        stream = iris_client.bulkdataselect(bk,
            minimumlength=(endtime - starttime) * 0.9)
    except:
        stream = []
    for tr in stream:
        if not tr.stats.npts or (tr.stats.endtime - tr.stats.starttime) < \
                minimum_duration:
            continue
        save_trace_fct(tr)
        successful_downloads.append(tr.id)
        failed_downloads.remove(tr.id)
        if logger:
            logger.info("Successfully downloaded %s from IRIS." % tr.id)

    for chan in failed_downloads:
        msg = "Failed to download %s from %s to %s" % (chan, starttime,
            endtime)
        if not logger:
            warnings.warn(msg)
            continue
        logger.warning(msg)
