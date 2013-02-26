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

    events = events_info(request, input)

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

