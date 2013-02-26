import glob
from obspy import read, UTCDateTime
import os

from obspyDMT.util import locate


def quake_info(address, target):
    """
    Reads the info in quake file ("info" folder)
    """

    events = []
    target_add = locate(address, target)

    for k in range(0, len(target_add)):
        if not os.path.isfile(os.path.join(target_add[k], 'quake')):
            print '============================='
            print 'quake file could not be found'
            print 'Start Creating the quake file'
            print '============================='
            quake_create(address_info=target_add[k])
        quake_file_open = open(os.path.join(target_add[k], 'quake'), 'r')
        quake_file = quake_file_open.readlines()

        tmp = []

        for i in quake_file:
            for j in i.split():
                try:
                    tmp.append(float(j))
                except ValueError:
                    pass

        if len(tmp) < 20:
            print '====================='
            print 'Modify the quake file'
            print '====================='
            quake_modify(quake_item=tmp, address_info=target_add[k])

            quake_file_open = open(os.path.join(target_add[k], 'quake'), 'r')
            quake_file = quake_file_open.readlines()

            tmp = []

            for i in quake_file:
                for j in i.split():
                    try:
                        tmp.append(float(j))
                    except ValueError:
                        pass

        quake_d = {'year0': int(tmp[0]), 'julday0': int(tmp[1]), \
                'hour0': int(tmp[2]), 'minute0': int(tmp[3]), \
                'second0': int(tmp[4]), 'lat': float(tmp[6]), \
                'lon': float(tmp[7]), 'dp': float(tmp[8]), \
                'mag': float(tmp[9]), \
                'year1': int(tmp[10]), 'julday1': int(tmp[11]), \
                'hour1': int(tmp[14]), 'minute1': int(tmp[15]), \
                'second1': int(tmp[16]), \
                'year2': int(tmp[18]), 'julday2': int(tmp[19]), \
                'hour2': int(tmp[22]), 'minute2': int(tmp[23]), \
                'second2': int(tmp[24])}

        quake_t0 = UTCDateTime(year=quake_d['year0'],
            julday=quake_d['julday0'], hour=quake_d['hour0'],
            minute=quake_d['minute0'], second=quake_d['second0'])
        quake_t1 = UTCDateTime(year=quake_d['year1'],
            julday=quake_d['julday1'], hour=quake_d['hour1'],
            minute=quake_d['minute1'], second=quake_d['second1'])
        quake_t2 = UTCDateTime(year=quake_d['year2'],
            julday=quake_d['julday2'], hour=quake_d['hour2'],
            minute=quake_d['minute2'], second=quake_d['second2'])

        events.append({'author': 'NONE', 'datetime': quake_t0,\
                    'depth': quake_d['dp'],
                    'event_id': quake_file[5].split('-')[0].lstrip(),
                    'flynn_region': 'NONE',
                    'latitude': quake_d['lat'],
                    'longitude': quake_d['lon'],
                    'magnitude': quake_d['mag'],
                    'magnitude_type': 'NONE',
                    'origin_id': -12345.0,
                    't1': quake_t1,
                    't2': quake_t2})

    address_event = []
    for i in range(0, len(target_add)):
        address_event.append(os.path.dirname(target_add[i]))

    return events, address_event


def quake_create(address_info):
    """
    if there is not any quake file in the info folder
    then it will be created based on the data available
    in the BH_RAW or BH file
    """
    quake_file = open(os.path.join(address_info, 'quake'), 'w')

    address = os.path.normpath(os.path.join(address_info, '..'))

    if os.path.isdir(os.path.join(address, 'BH_RAW')):
        sta_address = os.path.join(address, 'BH_RAW')
    #elif os.path.isdir(os.path.join(address, 'BH')):
    else:
        sta_address = os.path.join(address, 'BH')

    ls_stas = glob.glob(os.path.join(sta_address, '*.*.*.*'))

    sta = read(ls_stas[0])[0]
    sta_stats = sta.stats

    try:
        quake_file.writelines(repr(sta_stats.starttime.year).rjust(15)\
                + repr(sta_stats.starttime.julday).rjust(15) + '\n')
        quake_file.writelines(repr(sta_stats.starttime.hour).rjust(15)\
                + repr(sta_stats.starttime.minute).rjust(15) + \
                repr(sta_stats.starttime.second).rjust(15) + \
                repr(sta_stats.starttime.microsecond).rjust(15) + '\n')
        quake_file.writelines(\
                ' ' * (15 - len('%.5f' % sta_stats.sac.evla)) + '%.5f' \
                % sta_stats.sac.evla + \
                ' ' * (15 - len('%.5f' % sta_stats.sac.evlo)) + '%.5f' \
                % sta_stats.sac.evlo + '\n')
        quake_file.writelines(\
                ' ' * (15 - len('%.5f' % abs(sta_stats.sac.evdp))) + '%.5f' \
                % abs(sta_stats.sac.evdp) + '\n')
        quake_file.writelines(\
                ' ' * (15 - len('%.5f' % abs(sta_stats.sac.mag))) + '%.5f' \
                % abs(sta_stats.sac.mag) + '\n')
        quake_file.writelines(\
                ' ' * (15 - len(address.split('/')[-1])) + \
                        address.split('/')[-1] + '-' + '\n')

        quake_file.writelines(repr(sta_stats.starttime.year).rjust(15)\
                + repr(sta_stats.starttime.julday).rjust(15) \
                + repr(sta_stats.starttime.month).rjust(15) \
                + repr(sta_stats.starttime.day).rjust(15) + '\n')
        quake_file.writelines(repr(sta_stats.starttime.hour).rjust(15)\
                + repr(sta_stats.starttime.minute).rjust(15) + \
                repr(sta_stats.starttime.second).rjust(15) + \
                repr(sta_stats.starttime.microsecond).rjust(15) + '\n')

        sta_stats_endtime = sta_stats.starttime + sta_stats.npts / \
            sta_stats.sampling_rate

        quake_file.writelines(repr(sta_stats_endtime.year).rjust(15)\
                + repr(sta_stats_endtime.julday).rjust(15) \
                + repr(sta_stats_endtime.month).rjust(15) \
                + repr(sta_stats_endtime.day).rjust(15) + '\n')
        quake_file.writelines(repr(sta_stats_endtime.hour).rjust(15)\
                + repr(sta_stats_endtime.minute).rjust(15) + \
                repr(sta_stats_endtime.second).rjust(15) + \
                repr(sta_stats_endtime.microsecond).rjust(15) + '\n')

    except Exception, e:
        print e
        quake_file.writelines(repr(sta_stats.starttime.year).rjust(15)\
                + repr(sta_stats.starttime.julday).rjust(15) + '\n')
        quake_file.writelines(repr(sta_stats.starttime.hour).rjust(15)\
                + repr(sta_stats.starttime.minute).rjust(15) + \
                repr(sta_stats.starttime.second).rjust(15) + \
                repr(sta_stats.starttime.microsecond).rjust(15) + '\n')
        quake_file.writelines(\
                ' ' * (15 - len('%.5f' % 0.0)) + '%.5f' \
                % 0.0 + \
                ' ' * (15 - len('%.5f' % 0.0)) + '%.5f' \
                % 0.0 + '\n')
        quake_file.writelines(\
                ' ' * (15 - len('%.5f' % abs(-12345.0))) + '%.5f' \
                % abs(-12345.0) + '\n')
        quake_file.writelines(\
                ' ' * (15 - len('%.5f' % abs(-12345.0))) + '%.5f' \
                % abs(-12345.0) + '\n')
        quake_file.writelines(\
                ' ' * (15 - len(address.split('/')[-1])) + \
                        address.split('/')[-1] + '-' + '\n')

        quake_file.writelines(repr(sta_stats.starttime.year).rjust(15)\
                + repr(sta_stats.starttime.julday).rjust(15) \
                + repr(sta_stats.starttime.month).rjust(15) \
                + repr(sta_stats.starttime.day).rjust(15) + '\n')
        quake_file.writelines(repr(sta_stats.starttime.hour).rjust(15)\
                + repr(sta_stats.starttime.minute).rjust(15) + \
                repr(sta_stats.starttime.second).rjust(15) + \
                repr(sta_stats.starttime.microsecond).rjust(15) + '\n')

        sta_stats_endtime = sta_stats.starttime + sta_stats.npts / \
            sta_stats.sampling_rate

        quake_file.writelines(repr(sta_stats_endtime.year).rjust(15)\
                + repr(sta_stats_endtime.julday).rjust(15) \
                + repr(sta_stats_endtime.month).rjust(15) \
                + repr(sta_stats_endtime.day).rjust(15) + '\n')
        quake_file.writelines(repr(sta_stats_endtime.hour).rjust(15)\
                + repr(sta_stats_endtime.minute).rjust(15) + \
                repr(sta_stats_endtime.second).rjust(15) + \
                repr(sta_stats_endtime.microsecond).rjust(15) + '\n')
    quake_file.close()


def quake_modify(quake_item, address_info):

    """
    if the quake file does not contain all the required parameters
    then it will be modified based on the data available
    in the BH_RAW or BH file
    """

    quake_file_new = open(os.path.join(address_info, 'quake'), 'w')

    address = os.path.normpath(os.path.join(address_info, '..'))

    if os.path.isdir(os.path.join(address, 'BH_RAW')):
        sta_address = os.path.join(address, 'BH_RAW')
    #elif os.path.isdir(os.path.join(address, 'BH')):
    else:
        sta_address = os.path.join(address, 'BH')

    ls_stas = glob.glob(os.path.join(sta_address, '*.*.*.*'))

    sta = read(ls_stas[0])[0]
    sta_stats = sta.stats

    try:
        quake_file_new.writelines(repr(int(quake_item[0])).rjust(15)
                + repr(int(quake_item[1])).rjust(15) + '\n')
        quake_file_new.writelines(repr(int(quake_item[2])).rjust(15)
                + repr(int(quake_item[3])).rjust(15) +
                repr(int(quake_item[4])).rjust(15) +
                repr(int(quake_item[5])).rjust(15) + '\n')
        quake_file_new.writelines(\
                ' ' * (15 - len('%.5f' % quake_item[6])) + '%.5f'
                % quake_item[6] +
                ' ' * (15 - len('%.5f' % quake_item[7])) + '%.5f'
                % quake_item[7] + '\n')
        quake_file_new.writelines(
                ' ' * (15 - len('%.5f' % abs(quake_item[8]))) + '%.5f'
                % abs(quake_item[8]) + '\n')
        quake_file_new.writelines(
                ' ' * (15 - len('%.5f' % abs(sta_stats.sac.mag))) + '%.5f'
                % abs(sta_stats.sac.mag) + '\n')
        quake_file_new.writelines(
                ' ' * (15 - len(address.split('/')[-1])) +
                        address.split('/')[-1] + '-' + '\n')

        quake_file_new.writelines(repr(sta_stats.starttime.year).rjust(15)
                + repr(sta_stats.starttime.julday).rjust(15)
                + repr(sta_stats.starttime.month).rjust(15)
                + repr(sta_stats.starttime.day).rjust(15) + '\n')
        quake_file_new.writelines(repr(sta_stats.starttime.hour).rjust(15)
                + repr(sta_stats.starttime.minute).rjust(15) +
                repr(sta_stats.starttime.second).rjust(15) +
                repr(sta_stats.starttime.microsecond).rjust(15) + '\n')

        sta_stats_endtime = sta_stats.starttime + sta_stats.npts / \
            sta_stats.sampling_rate

        quake_file_new.writelines(repr(sta_stats_endtime.year).rjust(15)
                + repr(sta_stats_endtime.julday).rjust(15)
                + repr(sta_stats_endtime.month).rjust(15)
                + repr(sta_stats_endtime.day).rjust(15) + '\n')
        quake_file_new.writelines(repr(sta_stats_endtime.hour).rjust(15)
                + repr(sta_stats_endtime.minute).rjust(15) +
                repr(sta_stats_endtime.second).rjust(15) +
                repr(sta_stats_endtime.microsecond).rjust(15) + '\n')

    except Exception, e:
        print e
        quake_file_new.writelines(repr(int(quake_item[0])).rjust(15)
                + repr(int(quake_item[1])).rjust(15) + '\n')
        quake_file_new.writelines(repr(int(quake_item[2])).rjust(15)
                + repr(int(quake_item[3])).rjust(15) +
                repr(int(quake_item[4])).rjust(15) +
                repr(int(quake_item[5])).rjust(15) + '\n')
        quake_file_new.writelines(
                ' ' * (15 - len('%.5f' % quake_item[6])) + '%.5f'
                % quake_item[6] +
                ' ' * (15 - len('%.5f' % quake_item[7])) + '%.5f'
                % quake_item[7] + '\n')
        quake_file_new.writelines(
                ' ' * (15 - len('%.5f' % abs(quake_item[8]))) + '%.5f'
                % abs(quake_item[8]) + '\n')
        quake_file_new.writelines(
                ' ' * (15 - len('%.5f' % abs(-12345.0))) + '%.5f'
                % abs(-12345.0) + '\n')
        quake_file_new.writelines(
                ' ' * (15 - len(address.split('/')[-1])) +
                        address.split('/')[-1] + '-' + '\n')

        quake_file_new.writelines(repr(sta_stats.starttime.year).rjust(15)
                + repr(sta_stats.starttime.julday).rjust(15)
                + repr(sta_stats.starttime.month).rjust(15)
                + repr(sta_stats.starttime.day).rjust(15) + '\n')
        quake_file_new.writelines(repr(sta_stats.starttime.hour).rjust(15)
                + repr(sta_stats.starttime.minute).rjust(15) +
                repr(sta_stats.starttime.second).rjust(15) +
                repr(sta_stats.starttime.microsecond).rjust(15) + '\n')

        sta_stats_endtime = sta_stats.starttime + \
            sta_stats.npts / sta_stats.sampling_rate

        quake_file_new.writelines(repr(sta_stats_endtime.year).rjust(15)
                + repr(sta_stats_endtime.julday).rjust(15)
                + repr(sta_stats_endtime.month).rjust(15)
                + repr(sta_stats_endtime.day).rjust(15) + '\n')
        quake_file_new.writelines(repr(sta_stats_endtime.hour).rjust(15)
                + repr(sta_stats_endtime.minute).rjust(15) +
                repr(sta_stats_endtime.second).rjust(15) +
                repr(sta_stats_endtime.microsecond).rjust(15) + '\n')
    quake_file_new.close()


def events_info(request, input):

    """
    Get the event(s) info for event-based or continuous requests
    """

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

