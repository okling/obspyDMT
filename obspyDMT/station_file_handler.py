import glob
from obspy import read
import os

from obspyDMT.util import locate


def read_station_event(address):

    """
    Reads the station_event file ("info" folder)
    """

    if address.split('/')[-1].split('.') == ['info']:
        target_add = [address]
    elif locate(address, 'info'):
        target_add = locate(address, 'info')
    else:
        print 'Error: There is no "info" folder in the address.'

    sta_ev = []

    for k in range(0, len(target_add)):
        sta_ev_tmp = []

        if os.path.isfile(os.path.join(target_add[k], 'station_event')):
            sta_file_open = open(os.path.join(target_add[k],\
                                                    'station_event'), 'r')
        else:
            create_station_event(address=target_add[k])
            sta_file_open = open(os.path.join(target_add[k],\
                                                    'station_event'), 'r')
        sta_file = sta_file_open.readlines()
        for i in sta_file:
            sta_ev_tmp.append(i.split(','))
        sta_ev.append(sta_ev_tmp)

    return sta_ev


def create_station_event(address):
    """
    Creates the station_event file ("info" folder)
    """
    print '====================================='
    print 'station_event could not be found'
    print 'Start Creating the station_event file'
    print '====================================='

    event_address = os.path.dirname(address)
    if os.path.isdir(os.path.join(event_address, 'BH_RAW')):
        sta_address = os.path.join(event_address, 'BH_RAW')
    elif os.path.isdir(os.path.join(event_address, 'BH')):
        sta_address = os.path.join(event_address, 'BH')
    ls_stas = glob.glob(os.path.join(sta_address, '*.*.*.*'))

    print len(ls_stas)
    for i in range(0, len(ls_stas)):
        print i,
        sta_file_open = open(os.path.join(address, 'station_event'), 'a')

        try:
            sta = read(ls_stas[i])[0]
        except Exception, e:
            print e
            print 'could not read the waveform data'

        sta_stats = sta.stats

        try:
            sta_info = sta_stats.network + ',' + sta_stats.station + ',' + \
                sta_stats.location + ',' + sta_stats.channel + ',' + \
                str(sta_stats.sac.stla) + ',' + str(sta_stats.sac.stlo) + ',' + \
                str(sta_stats.sac.stel) + ',' + str(sta_stats.sac.stdp) + ',' + \
                event_address.split('/')[-1] + ',' + \
                str(sta_stats.sac.evla) + ',' + str(sta_stats.sac.evlo) + ',' + \
                str(sta_stats.sac.evdp) + ',' + str(sta_stats.sac.mag) + ',' + \
                'iris' + ',' + '\n'
        except Exception, e:
            print e
            sta_info = sta_stats.network + ',' + sta_stats.station + ',' + \
                sta_stats.location + ',' + sta_stats.channel + ',' + \
                str(-12345.0) + ',' + str(-12345.0) + ',' + \
                str(-12345.0) + ',' + str(-12345.0) + ',' + \
                event_address.split('/')[-1] + ',' + \
                str(-12345.0) + ',' + str(-12345.0) + ',' + \
                str(-12345.0) + ',' + str(-12345.0) + ',' + \
                'iris' + ',' + '\n'

        sta_file_open.writelines(sta_info)
        sta_file_open.close()

    print '\n--------------------------'


def rm_duplicate(Sta_all, address):
    """
    Remove station duplicates and give back the required list for updating
    """
    sta_all = []
    saved = []

    for i in Sta_all:
        if i[2] == '--' or i[2] == '  ':
            i[2] = ''
        for j in range(0, len(i)):
            if i[j] != str(i[j]):
                i[j] = str(i[j])
        if len(i) == 7:
            sta_all.append(str(i[0] + '_' + i[1] + '_' + i[2] + '_' + \
                            i[3] + '_' + i[4] + '_' + i[5] + '_' + i[6]))
        elif len(i) == 8:
            sta_all.append(str(i[0] + '_' + i[1] + '_' + i[2] + '_' + \
                            i[3] + '_' + i[4] + '_' + i[5] + '_' + i[6]\
                             + '_' + i[7]))

    sta_ev = read_station_event(address)
    ls_saved_stas = sta_ev[0]

    for i in range(0, len(ls_saved_stas)):
        sta_info = ls_saved_stas[i]
        saved.append(sta_info[0] + '_' + sta_info[1] + '_' + \
                            sta_info[2] + '_' + sta_info[3])

    Stas_req = sta_all

    len_all_sta = len(sta_all)
    num = []
    for i in range(0, len(saved)):
        for j in range(0, len(Stas_req)):
            if saved[i] in Stas_req[j]:
                num.append(j)

    num.sort(reverse=True)
    for i in num:
        del Stas_req[i]

    for m in range(0, len(Stas_req)):
        Stas_req[m] = Stas_req[m].split('_')

    Stas_req.sort()

    print '------------------------------------------'
    print 'Info:'
    print 'Number of all saved stations:     ' + str(len(saved))
    print 'Number of all available stations: ' + str(len_all_sta)
    print 'Number of stations to update for: ' + str(len(Stas_req))
    print '------------------------------------------'

    return Stas_req
