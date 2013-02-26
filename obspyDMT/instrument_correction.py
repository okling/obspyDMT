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

