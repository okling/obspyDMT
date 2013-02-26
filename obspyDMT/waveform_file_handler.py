from obspy import read
import os

from obspyDMT.station_file_handler import read_station_event


def writesac_all(i, events, address_events):

    sta_ev = read_station_event(address_events[i])
    ls_saved_stas = []

    for j in range(0, len(sta_ev[0])):
        station_id = sta_ev[0][j][0] + '.' + sta_ev[0][j][1] + '.' + \
                     sta_ev[0][j][2] + '.' + sta_ev[0][j][3]
        ls_saved_stas.append(os.path.join(address_events[i], 'BH_RAW',\
                                station_id))
    for j in range(0, len(sta_ev[0])):
        try:
            st = read(ls_saved_stas[j])
            st[0].write(ls_saved_stas[j], format='SAC')
            tr = read(ls_saved_stas[j])[0]
            if sta_ev[0][j][4] != None:
                tr.stats['sac']['stla'] = float(sta_ev[0][j][4])
            if sta_ev[0][j][5] != None:
                tr.stats['sac']['stlo'] = float(sta_ev[0][j][5])
            if sta_ev[0][j][6] != None:
                tr.stats['sac']['stel'] = float(sta_ev[0][j][6])
            if sta_ev[0][j][7] != None:
                tr.stats['sac']['stdp'] = float(sta_ev[0][j][7])

            if sta_ev[0][j][9] != None:
                tr.stats['sac']['evla'] = float(sta_ev[0][j][9])
            if sta_ev[0][j][10] != None:
                tr.stats['sac']['evlo'] = float(sta_ev[0][j][10])
            if sta_ev[0][j][11] != None:
                tr.stats['sac']['evdp'] = float(sta_ev[0][j][11])
            if sta_ev[0][j][12] != None:
                tr.stats['sac']['mag'] = float(sta_ev[0][j][12])

            tr.write(ls_saved_stas[j], format='SAC')
        except Exception, e:
            print '\n'
            print e
            print ls_saved_stas[j]
            print '------------------'


def writesac(address_st, sta_info, ev_info):

    st = read(address_st)
    st[0].write(address_st, format='SAC')
    st = read(address_st)

    if sta_info['latitude'] != None:
        st[0].stats['sac']['stla'] = sta_info['latitude']
    if sta_info['longitude'] != None:
        st[0].stats['sac']['stlo'] = sta_info['longitude']
    if sta_info['elevation'] != None:
        st[0].stats['sac']['stel'] = sta_info['elevation']
    if sta_info['depth'] != None:
        st[0].stats['sac']['stdp'] = sta_info['depth']

    if ev_info['latitude'] != None:
        st[0].stats['sac']['evla'] = ev_info['latitude']
    if ev_info['longitude'] != None:
        st[0].stats['sac']['evlo'] = ev_info['longitude']
    if ev_info['depth'] != None:
        st[0].stats['sac']['evdp'] = ev_info['depth']
    if ev_info['magnitude'] != None:
        st[0].stats['sac']['mag'] = ev_info['magnitude']

    st[0].write(address_st, format='SAC')
