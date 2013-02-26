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


