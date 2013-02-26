from datetime import datetime
from obspy.arclink import Client as Client_arclink
from obspy.iris import Client as Client_iris
from obspy.neries import Client as Client_neries
from obspy.xseed import Parser
import os
import pickle
import pprocess

from obspyDMT.event_file_handler import quake_info
from obspyDMT.waveform_file_handler import writesac_all
from obspyDMT.util import get_folder_size


def IRIS_download_core(i, j, dic, type, len_events, events, add_event, Sta_req,
                       input):
    """
    XXX: Add documentation.
    """
    print '------------------'
    print type
    print 'IRIS-Event and Station Numbers are:'
    print "%i/%i-%i/%i-%s" % (i + 1, len(events), j + 1, len(Sta_req),
                              input["cha"])
    try:
        dummy = 'Initializing'
        client_iris = Client_iris()
        t11 = datetime.now()
        if Sta_req[j][2] == '--' or Sta_req[j][2] == '  ':
                Sta_req[j][2] = ''

        if input['waveform'] == 'Y':
            dummy = 'Waveform'
            client_iris.saveWaveform(os.path.join(add_event[i], 'BH_RAW',
                                     Sta_req[j][0] + '.' +
                                     Sta_req[j][1] + '.' +
                                     Sta_req[j][2] + '.' + Sta_req[j][3]),
                                     Sta_req[j][0], Sta_req[j][1],
                                     Sta_req[j][2], Sta_req[j][3],
                                     events[i]['t1'], events[i]['t2'])
            print "Saving Waveform for: " + Sta_req[j][0] + \
                '.' + Sta_req[j][1] + '.' + \
                Sta_req[j][2] + '.' + Sta_req[j][3] + "  ---> DONE"

        if input['response'] == 'Y':
            dummy = 'Response'
            client_iris.saveResponse(os.path.join(add_event[i],
                                     'Resp', 'RESP' + '.' +
                                     Sta_req[j][0] + '.' +
                                     Sta_req[j][1] + '.' +
                                     Sta_req[j][2] + '.' + Sta_req[j][3]),
                                     Sta_req[j][0], Sta_req[j][1],
                                     Sta_req[j][2], Sta_req[j][3],
                                     events[i]['t1'], events[i]['t2'])
            print "Saving Response for: " + Sta_req[j][0] + \
                '.' + Sta_req[j][1] + '.' + \
                Sta_req[j][2] + '.' + Sta_req[j][3] + "  ---> DONE"

        if input['paz'] == 'Y':
            dummy = 'PAZ'
            client_iris.sacpz(Sta_req[j][0], Sta_req[j][1],
                              Sta_req[j][2], Sta_req[j][3],
                              events[i]['t1'], events[i]['t2'],
                              filename=os.path.join(add_event[i], 'Resp',
                              'PAZ' + '.' + Sta_req[j][0] + '.' +
                              Sta_req[j][1] + '.' +
                              Sta_req[j][2] + '.' +
                              Sta_req[j][3] + '.' + 'full'))
            print "Saving PAZ for     : " + Sta_req[j][0] + \
                '.' + Sta_req[j][1] + '.' + \
                Sta_req[j][2] + '.' + Sta_req[j][3] + "  ---> DONE"

        dummy = 'Meta-data'
        dic[j] = {'info': Sta_req[j][0] + '.' + Sta_req[j][1] +
                  '.' + Sta_req[j][2] + '.' + Sta_req[j][3],
                  'net': Sta_req[j][0], 'sta': Sta_req[j][1],
                  'latitude': Sta_req[j][4], 'longitude': Sta_req[j][5],
                  'loc': Sta_req[j][2], 'cha': Sta_req[j][3],
                  'elevation': Sta_req[j][6], 'depth': 0}

        Syn_file = open(os.path.join(add_event[i], 'info', 'station_event'),
                        'a')
        syn = dic[j]['net'] + ',' + dic[j]['sta'] + ',' + \
            dic[j]['loc'] + ',' + dic[j]['cha'] + ',' + \
            dic[j]['latitude'] + ',' + dic[j]['longitude'] + \
            ',' + dic[j]['elevation'] + ',' + '0' + ',' + \
            events[i]['event_id'] + ',' + str(events[i]['latitude']) \
            + ',' + str(events[i]['longitude']) + ',' + \
            str(events[i]['depth']) + ',' + \
            str(events[i]['magnitude']) + ',' + 'iris' + ',' + '\n'
        Syn_file.writelines(syn)
        Syn_file.close()
        '''
        if input['SAC'] == 'Y':
            writesac(address_st = os.path.join(add_event[i], 'BH_RAW', \
                Sta_req[j][0] + '.' + Sta_req[j][1] + '.' + \
                Sta_req[j][2] + '.' + Sta_req[j][3]), \
                sta_info = dic[j], ev_info = events[i])
        '''
        print "Saving Metadata for: " + Sta_req[j][0] + \
            '.' + Sta_req[j][1] + '.' + \
            Sta_req[j][2] + '.' + Sta_req[j][3] + "  ---> DONE"

        t22 = datetime.now()

        if input['time_iris'] == 'Y':
            time_iris = t22 - t11
            time_file = open(os.path.join(add_event[i], 'info', 'time_iris'),
                             'a')
            size = get_folder_size(os.path.join(add_event[i]))
            print size / 1024 ** 2
            ti = Sta_req[j][0] + ',' + Sta_req[j][1] + ',' + \
                Sta_req[j][2] + ',' + Sta_req[j][3] + ',' + \
                str(time_iris.seconds) + ',' + str(time_iris.microseconds) \
                + ',' + str(size / 1024 ** 2) + ',+,\n'
            time_file.writelines(ti)
            time_file.close()
    except Exception as e:

        t22 = datetime.now()

        if input['time_iris'] == 'Y':
            time_iris = t22 - t11
            time_file = open(os.path.join(add_event[i], 'info', 'time_iris'),
                             'a')
            size = get_folder_size(os.path.join(add_event[i]))
            print size / 1024 ** 2
            ti = Sta_req[j][0] + ',' + Sta_req[j][1] + ',' + \
                Sta_req[j][2] + ',' + Sta_req[j][3] + ',' + \
                str(time_iris.seconds) + ',' + \
                str(time_iris.microseconds) + ',' + \
                str(size ** 1024) + ',-,\n'
            time_file.writelines(ti)
            time_file.close()

        if Sta_req[j]:
            print dummy + '---' + Sta_req[j][0] + '.' + Sta_req[j][1] + \
                '.' + Sta_req[j][2] + '.' + Sta_req[j][3]
            ee = 'iris -- ' + dummy + '---' + str(i) + '-' + str(j) + '---' + \
                Sta_req[j][0] + '.' + Sta_req[j][1] + '.' + \
                Sta_req[j][2] + '.' + Sta_req[j][3] + \
                '---' + str(e) + '\n'
        elif Sta_req[j]:
            ee = 'There is no available station for this event.'

        Exception_file = open(os.path.join(add_event[i], 'info', 'exception'),
                              'a')
        Exception_file.writelines(ee)
        Exception_file.close()
        print e


def ARC_waveform(events, input, Sta_req, i, type):

    """
    Gets Waveforms, Response files and meta-data
    from ArcLink based on the requested events...
    """
    t_wave_1 = datetime.now()

    add_event = []

    if type == 'save':
        Period = input['min_date'].split('T')[0] + '_' + \
            input['max_date'].split('T')[0] + '_' + \
            str(input['min_mag']) + '_' + str(input['max_mag'])
        eventpath = os.path.join(input['datapath'], Period)
        for k in range(0, len(events)):
            add_event.append(os.path.join(eventpath, events[k]['event_id']))
    elif type == 'update':
        events, add_event = quake_info(input['arc_update'], target='info')

    len_events = len(events)

    if input['test'] == 'Y':
        len_req_arc = input['test_num']

    else:
        len_req_arc = len(Sta_req)

    dic = {}

    if input['req_parallel'] == 'Y':

        print "################"
        print "Parallel Request"
        print "################"

        parallel_results = pprocess.Map(limit=input['req_np'], reuse=1)
        parallel_job = \
            parallel_results.manage(pprocess.MakeReusable(ARC_download_core))

        for j in range(0, len_req_arc):
            parallel_job(i=i, j=j, dic=dic, type=type,
                         len_events=len_events,
                         events=events, add_event=add_event,
                         Sta_req=Sta_req, input=input)

        parallel_results.finish()

    else:

        for j in range(0, len_req_arc):
            ARC_download_core(i=i, j=j, dic=dic, type=type,
                              len_events=len_events,
                              events=events, add_event=add_event,
                              Sta_req=Sta_req, input=input)

    if input['SAC'] == 'Y':
        print '\n Converting the MSEED files to SAC...',
        writesac_all(i=i, events=events, address_events=add_event)
        print 'DONE\n'

    Report = open(os.path.join(add_event[i], 'info', 'report_st'), 'a')
    eventsID = events[i]['event_id']
    Report.writelines('<><><><><><><><><><><><><><><><><>' + '\n')
    Report.writelines(eventsID + '\n')
    Report.writelines('---------------ARC---------------' + '\n')
    Report.writelines('---------------' + input['cha'] + '---------------' +
                      '\n')
    rep = 'ARC-Available stations for channel ' + input['cha'] + \
        ' and for event' + '-' + str(i) + ': ' + str(len(Sta_req)) + '\n'
    Report.writelines(rep)
    rep = 'ARC-' + type + ' stations for channel ' + \
        input['cha'] + ' and for event' + '-' + \
        str(i) + ':     ' + str(len(dic)) + '\n'
    Report.writelines(rep)
    Report.writelines('----------------------------------' + '\n')

    t_wave_2 = datetime.now()
    t_wave = t_wave_2 - t_wave_1

    rep = "Time for " + type + "ing Waveforms from ArcLink: " + \
        str(t_wave) + '\n'
    Report.writelines(rep)
    Report.writelines('----------------------------------' + '\n')
    Report.close()

    if input['req_parallel'] == 'Y':
        report_parallel_open = open(os.path.join(add_event[i],
                                    'info', 'report_parallel'), 'a')
        report_parallel_open.writelines(
            '---------------ARC---------------' + '\n')
        report_parallel_open.writelines(
            'Request' + '\n')
        report_parallel_open.writelines(
            'Number of Nodes: ' + str(input['req_np']) + '\n')

        size = get_folder_size(os.path.join(add_event[i]))
        ti = str(t_wave.seconds) + ',' + str(t_wave.microseconds) \
            + ',' + str(size/1.e6) + ',+,\n'

        report_parallel_open.writelines(
            'Total Time     : ' + str(t_wave) + '\n')
        report_parallel_open.writelines(ti)
        report_parallel_open.close()

    print "\n------------------------"
    print 'ArcLink for event-' + str(i+1) + ' is Done'
    print 'Time:'
    print t_wave
    print "------------------------\n"


def ARC_download_core(i, j, dic, type, len_events, events, add_event, Sta_req,
                      input):
    """
    XXX: Add documentation.
    """
    print '------------------'
    print type
    print 'ArcLink-Event and Station Numbers are:'
    print str(i + 1) + '/' + str(len_events) + '-' + str(j + 1) + '/' + \
        str(len(Sta_req)) + '-' + input['cha']

    try:
        dummy = 'Initializing'

        client_arclink = Client_arclink(timeout=5)

        t11 = datetime.now()

        if input['waveform'] == 'Y':
            dummy = 'Waveform'

            try:
                client_arclink.saveWaveform(os.path.join(add_event[i],
                                            'BH_RAW', Sta_req[j][0] + '.' +
                                            Sta_req[j][1] + '.' +
                                            Sta_req[j][2] + '.' +
                                            Sta_req[j][3]), Sta_req[j][0],
                                            Sta_req[j][1], Sta_req[j][2],
                                            Sta_req[j][3], events[i]['t1'],
                                            events[i]['t2'])
            except Exception as e:
                print e

                if input['NERIES'] == 'Y':
                    client_neries = Client_neries()
                    print "\nWaveform is not available in ArcLink, " + \
                        "trying NERIES!\n"
                    client_neries.saveWaveform(os.path.join(add_event[i],
                                               'BH_RAW', Sta_req[j][0] +
                                               '.' + Sta_req[j][1] + '.' +
                                               Sta_req[j][2] + '.' +
                                               Sta_req[j][3]), Sta_req[j][0],
                                               Sta_req[j][1], Sta_req[j][2],
                                               Sta_req[j][3], events[i]['t1'],
                                               events[i]['t2'])

            check_file = open(os.path.join(add_event[i], 'BH_RAW',
                              Sta_req[j][0] + '.' + Sta_req[j][1] + '.' +
                              Sta_req[j][2] + '.' + Sta_req[j][3]))
            check_file.close()

            print "Saving Waveform for: " + Sta_req[j][0] + \
                '.' + Sta_req[j][1] + '.' + \
                Sta_req[j][2] + '.' + Sta_req[j][3] + "  ---> DONE"

        if input['response'] == 'Y':
            dummy = 'Response'

            client_arclink.saveResponse(os.path.join(add_event[i],
                                        'Resp', 'RESP' + '.' + Sta_req[j][0] +
                                        '.' + Sta_req[j][1] + '.' +
                                        Sta_req[j][2] + '.' + Sta_req[j][3]),
                                        Sta_req[j][0], Sta_req[j][1],
                                        Sta_req[j][2], Sta_req[j][3],
                                        events[i]['t1'], events[i]['t2'])

            sp = Parser(os.path.join(add_event[i],
                        'Resp', 'RESP' + '.' + Sta_req[j][0] +
                        '.' + Sta_req[j][1] + '.' +
                        Sta_req[j][2] + '.' + Sta_req[j][3]))

            sp.writeRESP(os.path.join(add_event[i], 'Resp'))

            print "Saving Response for: " + Sta_req[j][0] + \
                '.' + Sta_req[j][1] + '.' + \
                Sta_req[j][2] + '.' + Sta_req[j][3] + "  ---> DONE"

        if input['paz'] == 'Y':
            dummy = 'PAZ'

            paz_arc = client_arclink.getPAZ(Sta_req[j][0], Sta_req[j][1],
                                            Sta_req[j][2], Sta_req[j][3],
                                            time=events[i]['t1'])

            paz_file = open(os.path.join(add_event[i], 'Resp', 'PAZ' + '.' +
                            Sta_req[j][0] + '.' + Sta_req[j][1] + '.' +
                            Sta_req[j][2] + '.' +
                            Sta_req[j][3] + '.' + 'paz'), 'w')
            pickle.dump(paz_arc, paz_file)
            paz_file.close()

            print "Saving PAZ for     : " + Sta_req[j][0] + \
                '.' + Sta_req[j][1] + '.' + \
                Sta_req[j][2] + '.' + Sta_req[j][3] + "  ---> DONE"

        dummy = 'Meta-data'

        dic[j] = {'info': Sta_req[j][0] + '.' + Sta_req[j][1] +
                  '.' + Sta_req[j][2] + '.' + Sta_req[j][3],
                  'net': Sta_req[j][0], 'sta': Sta_req[j][1],
                  'latitude': Sta_req[j][4], 'longitude': Sta_req[j][5],
                  'loc': Sta_req[j][2], 'cha': Sta_req[j][3],
                  'elevation': Sta_req[j][6], 'depth': Sta_req[j][7]}

        Syn_file = open(os.path.join(add_event[i], 'info', 'station_event'),
                        'a')
        syn = Sta_req[j][0] + ',' + Sta_req[j][1] + ',' + \
            Sta_req[j][2] + ',' + Sta_req[j][3] + ',' + \
            str(Sta_req[j][4]) + ',' + str(Sta_req[j][5]) + \
            ',' + str(Sta_req[j][6]) + ',' + \
            str(Sta_req[j][7]) + ',' + events[i]['event_id'] + \
            ',' + str(events[i]['latitude']) \
            + ',' + str(events[i]['longitude']) + ',' + \
            str(events[i]['depth']) + ',' + \
            str(events[i]['magnitude']) + ',' + 'arc' + ',' + '\n'
        Syn_file.writelines(syn)
        Syn_file.close()
        print "Saving Station  for: " + Sta_req[j][0] + '.' + \
            Sta_req[j][1] + '.' + \
            Sta_req[j][2] + '.' + Sta_req[j][3] + "  ---> DONE"

        t22 = datetime.now()

        if input['time_arc'] == 'Y':
            time_arc = t22 - t11
            time_file = open(os.path.join(add_event[i], 'info', 'time_arc'),
                             'a+')
            size = get_folder_size(os.path.join(add_event[i]))
            print size / 1024 ** 2
            ti = Sta_req[j][0] + ',' + Sta_req[j][1] + ',' + \
                Sta_req[j][2] + ',' + Sta_req[j][3] + ',' + \
                str(time_arc.seconds) + ',' + \
                str(time_arc.microseconds) + ',' + \
                str(size / 1024 ** 2) + ',+,\n'
            time_file.writelines(ti)
            time_file.close()

    except Exception, e:

        t22 = datetime.now()

        if input['time_arc'] == 'Y':
            time_arc = t22 - t11
            time_file = open(os.path.join(add_event[i], 'info', 'time_arc'),
                             'a')
            size = get_folder_size(os.path.join(add_event[i]))
            print size / 1024 ** 2
            ti = Sta_req[j][0] + ',' + Sta_req[j][1] + ',' + \
                Sta_req[j][2] + ',' + Sta_req[j][3] + ',' + \
                str(time_arc.seconds) + ',' + \
                str(time_arc.microseconds) + ',' + \
                str(size / 1024 ** 2) + ',-,\n'
            time_file.writelines(ti)
            time_file.close()

        if len(Sta_req[j]) != 0:
            print dummy + '---' + Sta_req[j][0] + '.' + Sta_req[j][1] + \
                '.' + Sta_req[j][2] + '.' + Sta_req[j][3]
            ee = 'arclink -- ' + dummy + '---' + str(i) + '-' + str(j) + \
                '---' + Sta_req[j][0] + '.' + Sta_req[j][1] + '.' + \
                Sta_req[j][2] + '.' + Sta_req[j][3] + \
                '---' + str(e) + '\n'
        elif len(Sta_req[j]) == 0:
            ee = 'There is no available station for this event.'

        Exception_file = open(os.path.join(add_event[i], 'info', 'exception'),
                              'a')
        Exception_file.writelines(ee)
        Exception_file.close()
        print e
