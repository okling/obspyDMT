import fnmatch
from obspy import read
# XXX: Change to gps2distance
from obspy.core.util import locations2degrees
import math
import matplotlib.pyplot as plt
import numpy as np
import os
import random

from obspyDMT.event_file_handler import quake_info
from obspyDMT.station_file_handler import read_station_event


try:
    from mpl_toolkits.basemap import Basemap
except ImportError as error:
    print('Basemap: ' + 'not installed' + '\n\n' + \
                    'error:' + '\n' + str(error) + '\n' + \
                    'You could not use the Plot module')


def PLOT(input, clients):

    """
    Plotting tools
    """

    for i in ['plot_se', 'plot_sta', 'plot_ev', 'plot_ray',
                'plot_ray_gmt', 'plot_epi', 'plot_dt']:
        if input[i] != 'N':
            events, address_events = quake_info(input[i], 'info')

    ls_saved_stas = []
    ls_add_stas = []

    for k in ['plot_se', 'plot_sta', 'plot_ev', 'plot_ray', 'plot_ray_gmt', \
                'plot_epi']:
        if input[k] != 'N':
            for i in range(0, len(events)):

                ls_saved_stas_tmp = []
                ls_add_stas_tmp = []
                sta_ev = read_station_event(address_events[i])

                for j in range(0, len(sta_ev[0])):

                    if input['plot_type'] == 'raw':
                        BH_file = 'BH_RAW'
                        network = sta_ev[0][j][0]
                    elif input['plot_type'] == 'corrected':
                        if input['corr_unit'] == 'DIS':
                            BH_file = 'BH'
                            network = 'dis'
                        elif input['corr_unit'] == 'VEL':
                            BH_file = 'BH_' + input['corr_unit']
                            network = 'vel'
                        elif input['corr_unit'] == 'ACC':
                            BH_file = 'BH_' + input['corr_unit']
                            network = 'acc'

                    station_id = network + ',' + sta_ev[0][j][1] + ',' + \
                         sta_ev[0][j][2] + ',' + sta_ev[0][j][3] + ',' + \
                         sta_ev[0][j][4] + ',' + sta_ev[0][j][5] + ',' + \
                         sta_ev[0][j][6] + ',' + sta_ev[0][j][7] + ',' + \
                         sta_ev[0][j][8] + ',' + sta_ev[0][j][9] + ',' + \
                         sta_ev[0][j][10] + ',' + sta_ev[0][j][11] + ',' + \
                         sta_ev[0][j][12] + ',' + sta_ev[0][j][13]

                    if input['plot_all'] != 'Y':
                        if clients == sta_ev[0][j][13]:
                            ls_saved_stas_tmp.append(station_id)
                            ls_add_stas_tmp.append(\
                                        os.path.join(address_events[i], \
                                        BH_file, network + '.' + \
                                        sta_ev[0][j][1] + '.' + \
                                        sta_ev[0][j][2] + '.' + \
                                        sta_ev[0][j][3]))
                    elif input['plot_all'] == 'Y':
                        ls_saved_stas_tmp.append(station_id)
                        ls_add_stas_tmp.append(\
                                os.path.join(address_events[i], \
                                BH_file, network + '.' + \
                                sta_ev[0][j][1] + '.' + \
                                sta_ev[0][j][2] + '.' + \
                                sta_ev[0][j][3]))

                ls_saved_stas.append(ls_saved_stas_tmp)
                ls_add_stas.append(ls_add_stas_tmp)

            for i in range(0, len(ls_saved_stas)):
                for j in range(0, len(ls_saved_stas[i])):
                    ls_saved_stas[i][j] = ls_saved_stas[i][j].split(',')

    for i in ['plot_se', 'plot_sta', 'plot_ev', 'plot_ray']:
        if input[i] != 'N':
            plot_se_ray(input, ls_saved_stas)

    if input['plot_ray_gmt'] != 'N':
        plot_ray_gmt(input, ls_saved_stas)

    if input['plot_epi'] != 'N':
        plot_epi(input, ls_add_stas, ls_saved_stas)

    if input['plot_dt'] != 'N':
        plot_dt(input, address_events)


def plot_se_ray(input, ls_saved_stas):

    """
    Plot: station, event, both and ray path
    """

    plt.clf()

    m = Basemap(projection='aeqd', lon_0=-100, lat_0=40, \
                                                resolution='c')

    m.drawcoastlines()
    #m.fillcontinents()
    m.drawparallels(np.arange(-90., 120., 30.))
    m.drawmeridians(np.arange(0., 420., 60.))
    m.drawmapboundary()

    pattern_sta = input['sta'] + '.' + input['loc'] + '.' + input['cha']

    for i in range(0, len(ls_saved_stas)):
        print str(i + 1) + '/' + str(len(ls_saved_stas))
        print '---------'

        ls_stas = ls_saved_stas[i]

        if not input['evlatmin'] <= float(ls_stas[0][9]) \
                <= input['evlatmax'] or \
           not input['evlonmin'] <= float(ls_stas[0][10]) \
               <= input['evlonmax'] or \
           not input['max_depth'] <= float(ls_stas[0][11]) \
               <= input['min_depth'] or \
           not input['min_mag'] <= float(ls_stas[0][12]) \
               <= input['max_mag']:
            continue

        if input['plot_se'] != 'N' or \
                            input['plot_ev'] != 'N' or \
                            input['plot_ray'] != 'N':
            x_ev, y_ev = m(float(ls_stas[0][10]), \
                           float(ls_stas[0][9]))
            m.scatter(x_ev, y_ev, \
                        math.log(float(ls_stas[0][12])) ** 6, \
                        color="red", marker="o", \
                        edgecolor="black", zorder=10)

        for j in range(0, len(ls_stas)):
            try:

                station_name = ls_stas[j][1] + '.' + ls_stas[j][2] + \
                            '.' + ls_stas[j][3]

                if not fnmatch.fnmatch(station_name, pattern_sta):
                    continue

                if not input['mlat_rbb'] <= float(ls_stas[j][4]) <= \
                        input['Mlat_rbb'] or \
                    not input['mlon_rbb'] <= float(ls_stas[j][5]) <= \
                        input['Mlon_rbb']:
                    continue

                st_lat = float(ls_stas[j][4])
                st_lon = float(ls_stas[j][5])
                ev_lat = float(ls_stas[j][9])
                ev_lon = float(ls_stas[j][10])

                if input['plot_ray'] != 'N':
                    m.drawgreatcircle(ev_lon, ev_lat, st_lon, st_lat,
                        alpha=0.1)

                if input['plot_se'] != 'N' or input['plot_sta'] != 'N' or \
                    input['plot_ray'] != 'N':
                    x_sta, y_sta = m(st_lon, st_lat)
                    m.scatter(x_sta, y_sta, 20, color='blue', marker="o",
                                            edgecolor="black", zorder=10)

            except Exception as e:
                print e

    print 'Saving the plot in the following address:'
    print input['plot_save'] + 'plot.' + input['plot_format']

    plt.savefig(os.path.join(input['plot_save'], 'plot.' + \
                                                input['plot_format']))


def plot_ray_gmt(input, ls_saved_stas):

    """
    Plot: stations, events and ray paths for the specified directory using GMT
    """
    evsta_info_open = open(os.path.join(input['plot_save'], 'evsta_info.txt'),
        'w')
    evsta_plot_open = open(os.path.join(input['plot_save'], 'evsta_plot.txt'),
        'w')
    ev_plot_open = open(os.path.join(input['plot_save'], 'ev_plot.txt'), 'w')
    sta_plot_open = open(os.path.join(input['plot_save'], 'sta_plot.txt'), 'w')

    ls_sta = []

    for i in range(0, len(ls_saved_stas)):
        print str(i + 1) + '/' + str(len(ls_saved_stas))
        print '---------'

        ls_stas = ls_saved_stas[i]

        if not input['evlatmin'] <= float(ls_stas[0][9]) <= \
                input['evlatmax'] or \
            not input['evlonmin'] <= float(ls_stas[0][10]) <= \
                input['evlonmax'] or \
            not input['max_depth'] <= float(ls_stas[0][11]) <= \
                input['min_depth'] or \
            not input['min_mag'] <= float(ls_stas[0][12]) <= input['max_mag']:
            continue

        ev_plot_open.writelines(str(round(float(ls_stas[0][10]), 5)) + ' ' +
                                str(round(float(ls_stas[0][9]), 5)) + ' \n')

        pattern_sta = input['sta'] + '.' + input['loc'] + '.' + input['cha']

        for j in range(0, len(ls_stas)):

            station_name = ls_stas[j][1] + '.' + ls_stas[j][2] + \
                                '.' + ls_stas[j][3]
            station_ID = ls_stas[j][0] + '.' + station_name

            if not fnmatch.fnmatch(station_name, pattern_sta):
                continue

            if not input['mlat_rbb'] <= float(ls_stas[j][4]) <= \
                    input['Mlat_rbb'] or \
               not input['mlon_rbb'] <= float(ls_stas[j][5]) <= \
                   input['Mlon_rbb']:
                continue

            evsta_info_open.writelines(ls_stas[j][8] + ' , ' + station_ID +
                ' , \n')

            evsta_plot_open.writelines(
                '> -G' + str(int(random.random() * 256)) + '/' +
                str(int(random.random() * 256)) + '/' +
                str(int(random.random() * 256)) + '\n' +
                str(round(float(ls_stas[j][10]), 5)) + ' ' +
                str(round(float(ls_stas[j][9]), 5)) + ' ' +
                str(random.random()) + ' ' +
                '\n' +
                str(round(float(ls_stas[j][5]), 5)) + ' ' +
                str(round(float(ls_stas[j][4]), 5)) + ' ' +
                str(random.random()) + ' ' +
                '\n')

            if ls_sta == [] or not station_ID in ls_sta[:][0]:
                ls_sta.append([station_ID, \
                    [str(round(float(ls_stas[j][4]), 5)), \
                     str(round(float(ls_stas[j][5]), 5))]])

    for k in range(0, len(ls_sta)):
        sta_plot_open.writelines(\
                str(round(float(ls_sta[k][1][1]), 5)) + ' ' + \
                str(round(float(ls_sta[k][1][0]), 5)) + ' ' + \
                '\n')

    evsta_info_open.close()
    evsta_plot_open.close()
    ev_plot_open.close()
    sta_plot_open.close()

    pwd_str = os.getcwd()

    os.chdir(input['plot_save'])

    os.system('psbasemap -Rd -JK180/9i -B45g30 -K > output.ps')
    os.system('pscoast -Rd -JK180/9i -B45g30:."World-wide Ray Path Coverage":'
        ' -Dc -A1000 -Glightgray -Wthinnest -t20 -O -K >> output.ps')

    os.system('psxy ./evsta_plot.txt -JK180/9i -Rd -O -K -t100 >> output.ps')
    os.system('psxy ./sta_plot.txt -JK180/9i -Rd -Si0.14c -Gblue -O -K >> '
        'output.ps')
    os.system('psxy ./ev_plot.txt -JK180/9i -Rd -Sa0.28c -Gred -O >> '
        'output.ps')

    os.system('ps2raster output.ps -A -P -Tf')

    os.system('mv output.ps plot.ps')
    os.system('mv output.pdf plot.pdf')

    os.system('xdg-open plot.pdf')

    os.chdir(pwd_str)


def plot_epi(input, ls_add_stas, ls_saved_stas):

    """
    Plot: Epicentral distance-Time
    """

    plt.clf()

    for target in range(0, len(ls_add_stas)):
        print str(target + 1) + '/' + str(len(ls_add_stas))
        print '---------'

        for i in range(0, len(ls_add_stas[target])):

            try:

                tr = read(ls_add_stas[target][i])[0]
                tr.normalize()
                dist = locations2degrees(float(ls_saved_stas[target][i][9]), \
                            float(ls_saved_stas[target][i][10]), \
                            float(ls_saved_stas[target][i][4]), \
                            float(ls_saved_stas[target][i][5]))
                if input['min_epi'] <= dist <= input['max_epi']:
                    x = range(0, len(tr.data))
                    for i in range(0, len(x)):
                        x[i] = x[i] / float(tr.stats['sampling_rate'])
                    plt.plot(x, tr.data + dist, color='black')

            except Exception, e:
                print e
                pass

            plt.xlabel('Time (sec)')
            plt.ylabel('Epicentral distance (deg)')

    print 'Saving the plot in the following address:'
    print input['plot_save'] + 'plot.' + input['plot_format']

    plt.savefig(os.path.join(input['plot_save'], 'plot.' + \
                                                input['plot_format']))


def plot_dt(input, address_events):
    """
    Plot: Data(MB)-Time(Sec)
    """

    for i in range(0, len(address_events)):
        for client in ['time_iris', 'time_arc']:
            print address_events[i]
            if os.path.isfile(os.path.join(address_events[i], 'info', client)):

                plt.clf()

                dt_open = open(os.path.join(address_events[i], \
                                            'info', client))
                dt_read = dt_open.readlines()
                for j in range(0, len(dt_read)):
                    dt_read[j] = dt_read[j].split(',')

                time_single = 0
                succ = 0
                fail = 0
                MB_all = []
                time_all = []

                for k in range(0, len(dt_read)):

                    time_single += eval(dt_read[k][4]) + eval(dt_read[k][5]) \
                        / 1.e6
                    time_all.append(time_single)
                    MB_single = eval(dt_read[k][6])
                    MB_all.append(MB_single)

                    if dt_read[k][7] == '+':
                        single_succ = plt.scatter(time_single, MB_single, s=1,
                            c='b', edgecolors='b', marker='o',
                            label='Serial (successful)')
                        succ += 1
                    elif dt_read[k][7] == '-':
                        plt.scatter(time_single, MB_single, s=1, c='r',
                            edgecolors='r', marker='o',
                            label='Serial (failed)')
                        fail += 1

                if input['req_parallel'] == 'Y':
                    rep_par_open = open(os.path.join(address_events[i],
                                                    'info', 'report_parallel'))
                    rep_par_read = rep_par_open.readlines()
                    time_parallel = eval(rep_par_read[4].split(',')[0]) + \
                                    eval(rep_par_read[4].split(',')[1]) / 1.e6
                    MB_parallel = eval(rep_par_read[4].split(',')[2])
                    parallel_succ = plt.scatter(time_parallel, MB_parallel,
                        s=30, c='r', edgecolors='r', marker='o',
                        label='Parallel')

                time_array = np.array(time_all)
                MB_array = np.array(MB_all)

                poly = np.poly1d(np.polyfit(time_array, MB_array, 1))
                plt.plot(time_array, poly(time_array), 'k--')

                trans_rate = (poly(time_array[-1]) - poly(time_array[0])) / \
                    (time_array[-1] - time_array[0]) * 60

                plt.xlabel('Time (sec)', size='large', weight='bold')
                plt.ylabel('Stored Data (MB)', size='large', weight='bold')
                plt.xticks(size='large', weight='bold')
                plt.yticks(size='large', weight='bold')

                plt.title(client.split('_')[1].upper() + '\n' + \
                    'All: ' + str(succ + fail) + '--' + \
                    'Succ: ' + str(succ) + ' ' + '(' + \
                    str(round(float(succ) / (succ + fail) * 100., 1)) + '%)' +\
                    '-' + \
                    'Fail: ' + str(fail) + ' ' + '(' + \
                    str(round(float(fail) / (succ + fail) * 100., 1)) + '%)' +\
                    '--' + \
                     str(round(trans_rate, 2)) + 'MB/min', size='x-large')

                if input['req_parallel'] == 'Y':
                    plt.legend([single_succ, parallel_succ], \
                            ['Serial', 'Parallel'], loc=4)

                plt.savefig(os.path.join(address_events[i], 'info', \
                            'Data-Time_' + client.split('_')[1] + \
                            '.' + input['plot_format']))
