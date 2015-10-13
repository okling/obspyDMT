#!/usr/bin/env python
# -*- coding: utf-8 -*-

# -------------------------------------------------------------------
#   Filename:  metadata_handler.py
#   Purpose:   handling metadata in obspyDMT
#   Author:    Kasra Hosseini
#   Email:     hosseini@geophysik.uni-muenchen.de
#   License:   GNU Lesser General Public License, Version 3
# -------------------------------------------------------------------

# -----------------------------------------------------------------------
# ----------------Import required Modules (Python and Obspy)-------------
# -----------------------------------------------------------------------

# Required Python and Obspy modules will be imported in this part.
import copy
from datetime import datetime
import numpy as np
from obspy import UTCDateTime
try:
    from obspy.clients.arclink import Client as Client_arclink
except Exception, e:
    from obspy.arclink import Client as Client_arclink
try:
    from obspy.clients.fdsn import Client as Client_fdsn
except Exception, e:
    from obspy.fdsn import Client as Client_fdsn
import os
import pickle
import sys

from utility_codes import create_folders_files
from utility_codes import read_list_stas, calculate_time_phase
from utility_codes import read_station_event

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

# ###################### get_metadata ####################################


def get_metadata(input_dics, event, info_avail):
    """
    Retrieve meta-data information.
    :param input_dics:
    :param event:
    :param info_avail:
    :return:
    """
    print '\n============='
    print 'metadata mode'
    print '============='

    period = '{0:s}_{1:s}'.format(
        input_dics['min_date'].split('T')[0],
        input_dics['max_date'].split('T')[0])
    eventpath = os.path.join(input_dics['datapath'], period)

    t_1 = datetime.now()
    print 'Initializing folders and files...',
    create_folders_files(event, eventpath, input_dics)
    print 'DONE'
    target_path = os.path.join(eventpath, event['event_id'])

    if not input_dics['list_stas']:
        stas_all = []
        for cl in range(len(input_dics['data_source'])):
            if input_dics['data_source'][cl].lower() not in ['arclink']:
                stas_cli = fdsn_available(input_dics, cl,
                                          event, target_path)
            elif input_dics['data_source'][cl].lower() == 'arclink':
                stas_cli = arc_available(input_dics, event,
                                         target_path)
            else:
                sys.exit('ERROR: %s is not implemented!'
                         % input_dics['data_source'][cl])
            # put all the available stations together
            for st_fds in stas_cli:
                stas_all.append(st_fds)
    else:
        stas_all = read_list_stas(input_dics['list_stas'],
                                  input_dics['normal_mode_syn'],
                                  input_dics['specfem3D'])
        if input_dics['bulk']:
            fdsn_create_bulk_list(target_path, input_dics,
                                  stas_all, event)
    stas_arr = np.array(stas_all)
    np.save(os.path.join(target_path, 'info', 'availability'), stas_arr)
    np.savetxt(os.path.join(target_path, 'info', 'availability.txt'),
               stas_arr, delimiter=',', fmt='%s')
    stas_update = rm_duplicate(stas_all, target_path)
    stas_arr_update = np.array(stas_update)

    if not input_dics['bulk']:
        print '\navailability for event: %s ---> DONE' % info_avail
    else:
        print '\nbulkfile for event: %s ---> DONE' % info_avail

    print 'Time for checking the availability: %s' \
          % (datetime.now() - t_1)

    return stas_arr_update

# ##################### fdsn_available ##################################


def fdsn_available(input_dics, cl, event, target_path):
    """
    Check the availablity of FDSN stations
    :param input_dics:
    :param cl:
    :param event:
    :param target_path:
    :return:
    """
    print "Check the availability: %s" % input_dics['data_source'][cl]

    if input_dics['username']:
        include_restricted = True
    else:
        include_restricted = None

    sta_fdsn = []
    try:
        client_fdsn = Client_fdsn(base_url=input_dics['data_source'][cl],
                                  user=input_dics['username'],
                                  password=input_dics['password'])

        available = client_fdsn.get_stations(
            network=input_dics['net'],
            station=input_dics['sta'],
            location=input_dics['loc'],
            channel=input_dics['cha'],
            starttime=event['t1'],
            endtime=event['t2'],
            latitude=input_dics['lat_cba'],
            longitude=input_dics['lon_cba'],
            minradius=input_dics['mr_cba'],
            maxradius=input_dics['Mr_cba'],
            minlatitude=input_dics['mlat_rbb'],
            maxlatitude=input_dics['Mlat_rbb'],
            minlongitude=input_dics['mlon_rbb'],
            maxlongitude=input_dics['Mlon_rbb'],
            includerestricted=include_restricted,
            level='channel')

        for network in available.networks:
            for station in network:
                for channel in station:
                    st_id = '%s_%s_%s_%s' % (network.code,
                                             station.code,
                                             channel.location_code,
                                             channel.code)
                    sta_fdsn.append([network.code, station.code,
                                     channel.location_code, channel.code,
                                     channel.latitude, channel.longitude,
                                     channel.elevation, channel.depth,
                                     st_id, input_dics['data_source'][cl]])

        if input_dics['bulk']:
            print 'Start creating a list for bulk request'
            bulk_list = []
            for bulk_sta in sta_fdsn:
                if input_dics['cut_time_phase']:
                    t_start, t_end = calculate_time_phase(event, bulk_sta)
                else:
                    t_start = event['t1']
                    t_end = event['t2']
                bulk_list.append((bulk_sta[0], bulk_sta[1], bulk_sta[2],
                                  bulk_sta[3], t_start, t_end))

            bulk_list_fio = open(os.path.join(
                target_path, 'info',
                'bulkdata_list_%s' % input_dics['data_source'][cl]), 'a+')
            pickle.dump(bulk_list, bulk_list_fio)
            bulk_list_fio.close()

    except Exception as error:
        exc_file = open(os.path.join(target_path, 'info', 'exception'), 'a+')
        ee = 'availability -- %s -- %s\n' % (input_dics['data_source'][cl],
                                             error)
        exc_file.writelines(ee)
        exc_file.close()
        print 'ERROR: %s' % ee
        return []

    if len(sta_fdsn) == 0:
        sta_fdsn = []
    sta_fdsn.sort()
    return sta_fdsn

# ##################### arc_available ###################################


def arc_available(input_dics, event, target_path):
    """
    Check the availability of ArcLink stations
    :param input_dics:
    :param event:
    :param target_path:
    :return:
    """
    print "Check the availability: ArcLink"
    client_arclink = Client_arclink(user='test@obspy.org',
                                    timeout=input_dics['arc_avai_timeout'])
    sta_arc = []
    try:
        inventories = client_arclink.getInventory(
            network=input_dics['net'],
            station=input_dics['sta'],
            location=input_dics['loc'],
            channel=input_dics['cha'],
            starttime=UTCDateTime(event['t1']),
            endtime=UTCDateTime(event['t2']),
            min_latitude=input_dics['mlat_rbb'],
            max_latitude=input_dics['Mlat_rbb'],
            min_longitude=input_dics['mlon_rbb'],
            max_longitude=input_dics['Mlon_rbb'])

        for inv_key in inventories.keys():
            netsta = inv_key.split('.')
            if len(netsta) == 4:
                sta = '%s.%s' % (netsta[0], netsta[1])
                if not inventories[sta]['depth']:
                    inventories[sta]['depth'] = 0.0
                st_id = '%s_%s_%s_%s' % (netsta[0],
                                         netsta[1],
                                         netsta[2],
                                         netsta[3])
                sta_arc.append([netsta[0], netsta[1], netsta[2], netsta[3],
                                inventories[sta]['latitude'],
                                inventories[sta]['longitude'],
                                inventories[sta]['elevation'],
                                inventories[sta]['depth'],
                                st_id, 'ARCLINK'])

    except Exception as error:
        exc_file = open(os.path.join(target_path, 'info', 'exception'), 'a+')
        ee = 'availability -- arclink -- %s\n' % error
        exc_file.writelines(ee)
        exc_file.close()
        print 'ERROR: %s' % ee
        return []

    if len(sta_arc) == 0:
        sta_arc.append([])
    sta_arc.sort()
    return sta_arc

# ##################### fdsn_create_bulk_list ###############################


def fdsn_create_bulk_list(target_path, input_dics, stas_all, event):
    """
    Create bulkdata_list in case of --list_stas flag
    :param target_path:
    :param input_dics:
    :param stas_all:
    :param event:
    :return:
    """
    print 'Start creating a list for bulk request'
    bulk_list = []
    for bulk_sta in stas_all:
        if input_dics['cut_time_phase']:
            t_start, t_end = calculate_time_phase(event, bulk_sta)
        else:
            t_start = event['t1']
            t_end = event['t2']
        bulk_list.append((bulk_sta[0], bulk_sta[1], bulk_sta[2],
                          bulk_sta[3], t_start, t_end))

    bulk_list_fio = open(os.path.join(target_path, 'info',
                                      'bulkdata_list_local'), 'a+')
    pickle.dump(bulk_list, bulk_list_fio)
    bulk_list_fio.close()

# ##################### rm_duplicate ####################################


def rm_duplicate(all_sta_avail, address):
    """
    remove duplicates and give back the required list for updating
    """

    id_avai_stas = []
    for sta in all_sta_avail:
        if sta[2] == '--' or sta[2] == '  ':
            sta[2] = ''
        id_avai_stas.append('%s#%s#%s#%s#%s#%s#%s#%s#%s#%s'
                            % (sta[0], sta[1], sta[2], sta[3],
                               sta[4], sta[5], sta[6], sta[7],
                               sta[8], sta[9]))

    sta_ev_saved = read_station_event(address)

    id_all_saved_stas = []
    for saved_sta in sta_ev_saved[0]:
        id_all_saved_stas.append('%s#%s#%s#%s' % (saved_sta[0], saved_sta[1],
                                                  saved_sta[2], saved_sta[3]))

    stas_update = copy.deepcopy(id_avai_stas)
    del_num = []
    for saved_sta in id_all_saved_stas:
        for j in range(len(stas_update)):
            if saved_sta in stas_update[j]:
                del_num.append(j)

    del_num.sort(reverse=True)
    for dn in del_num:
        del stas_update[dn]

    for i in range(len(stas_update)):
        stas_update[i] = stas_update[i].split('#')

    stas_update.sort()
    print '------------------------------------------'
    print 'Info:'
    print 'Number of all saved stations:     %s' % len(id_all_saved_stas)
    print 'Number of all available stations: %s' % len(id_avai_stas)
    print 'Number of stations to update for: %s' % len(stas_update)
    print '------------------------------------------'

    return stas_update
