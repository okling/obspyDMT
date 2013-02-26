import fnmatch
import glob
from lxml import objectify
import os
import shutil
import sys
import tarfile


def get_folder_size(folder):
    """
    Returns the size of a folder in bytes.
    """
    total_size = os.path.getsize(folder)
    for item in os.listdir(folder):
        itempath = os.path.join(folder, item)
        if os.path.isfile(itempath):
            total_size += os.path.getsize(itempath)
        elif os.path.isdir(itempath):
            total_size += get_folder_size(itempath)
    return total_size


def locate(root='.', target='info'):
    """
    Locates a subdirectory within a directory.
    """
    matches = []

    for root, dirnames, filenames in os.walk(root):
        for dirnames in fnmatch.filter(dirnames, target):
            matches.append(os.path.join(root, dirnames))

    return matches


def compress_gzip(path, tar_file, files):
    """
    XXX: Add documentation
    """
    tar = tarfile.open(tar_file, "w:gz")
    os.chdir(path)

    for infile in glob.glob(os.path.join(path, files)):

        print 50 * "-"
        print "Compressing:"
        print infile

        tar.add(infile.split('/')[-1])
        os.remove(infile)

    tar.close()


def send_email(email_address, message):
    """
    Sending email to the specified "email" address
    """
    try:
        import smtplib
    except ImportError:
        print "smptlib is not installed. The following email was not sent:"
        print "To: %s" % email_address
        print message
        return

    fromaddr = 'obspyDMT'
    toaddrs = email_address

    server = smtplib.SMTP('localhost')
    server.sendmail(fromaddr, toaddrs, message)


def create_folders_files(events, eventpath):
    """
    Create required folders and files in the event folder(s)
    """
    for event in events:
        if os.path.exists(os.path.join(eventpath, event['event_id'])):
            input_str = ('Folder for -- the requested Period (min/max) '
                         'and Magnitude (min/max) -- exists in your '
                         'directory.\n\n'
                         'You could either close the program and try '
                         'updating your '
                         'folder OR remove the tree, continue the program '
                         'and download '
                         'again.\nDo you want to continue? (Y/N)\n')

            if raw_input(input_str).upper() == 'Y':
                print 50 * "-"
                shutil.rmtree(os.path.join(eventpath, event['event_id']))

            else:
                print '------------------------------------------------'
                print 'So...you decided to update your folder...Ciao'
                print '------------------------------------------------'
                sys.exit()

        try:
            os.makedirs(os.path.join(eventpath, event['event_id'],
                'BH_RAW'))
            os.makedirs(os.path.join(eventpath, event['event_id'], 'Resp'))
            os.makedirs(os.path.join(eventpath, event['event_id'], 'info'))
        except:
            pass

        # Create an empty file.
        open(os.path.join(eventpath, event['event_id'], 'info', 'report_st'),
            'a+').close()

        Exception_file = open(os.path.join(eventpath, event['event_id'],
            'info', 'exception'), 'a+')
        Exception_file.writelines('\n' + event["event_id"] + '\n')

        # Create empty file.
        open(os.path.join(eventpath, event['event_id'], 'info',
            'station_event'), 'a+').close()

        quake_file = open(os.path.join(eventpath, event['event_id'],
                            'info', 'quake'), 'a+')

        quake_file.writelines(repr(event['datetime'].year).rjust(15)
            + repr(event['datetime'].julday).rjust(15) + '\n')
        quake_file.writelines(repr(event['datetime'].hour).rjust(15)
            + repr(event['datetime'].minute).rjust(15) +
            repr(event['datetime'].second).rjust(15) +
            repr(event['datetime'].microsecond).rjust(15) + '\n')

        quake_file.writelines(
            ' ' * (15 - len('%.5f' % event['latitude'])) + '%.5f'
            % event['latitude'] +
            ' ' * (15 - len('%.5f' % event['longitude'])) + '%.5f'
            % event['longitude'] + '\n')
        quake_file.writelines(
            ' ' * (15 - len('%.5f' % abs(event['depth']))) + '%.5f'
            % abs(event['depth']) + '\n')
        quake_file.writelines(
            ' ' * (15 - len('%.5f' % abs(event['magnitude']))) + '%.5f'
            % abs(event['magnitude']) + '\n')
        quake_file.writelines(' ' * (15 - len(event['event_id'])) +
            event['event_id'] + '-' + '\n')

        quake_file.writelines(repr(event['t1'].year).rjust(15)
            + repr(event['t1'].julday).rjust(15)
            + repr(event['t1'].month).rjust(15)
            + repr(event['t1'].day).rjust(15) + '\n')
        quake_file.writelines(repr(event['t1'].hour).rjust(15)
            + repr(event['t1'].minute).rjust(15) +
            repr(event['t1'].second).rjust(15) +
            repr(event['t1'].microsecond).rjust(15) + '\n')

        quake_file.writelines(repr(event['t2'].year).rjust(15)
            + repr(event['t2'].julday).rjust(15)
            + repr(event['t2'].month).rjust(15)
            + repr(event['t2'].day).rjust(15) + '\n')
        quake_file.writelines(repr(event['t2'].hour).rjust(15)
            + repr(event['t2'].minute).rjust(15) +
            repr(event['t2'].second).rjust(15) +
            repr(event['t2'].microsecond).rjust(15) + '\n')


def XML_list_avail(xmlfile):
    """
    This module changes the XML file got from availability to a list
    """
    sta_obj = objectify.XML(xmlfile)
    sta_req = []

    for i in range(0, len(sta_obj.Station)):

        station = sta_obj.Station[i]
        net = station.get('net_code')
        sta = station.get('sta_code')

        lat = str(station.Lat)
        lon = str(station.Lon)
        ele = str(station.Elevation)

        for j in range(0, len(station.Channel)):
            cha = station.Channel[j].get('chan_code')
            loc = station.Channel[j].get('loc_code')

            sta_req.append([net, sta, loc, cha, lat, lon, ele])

    return sta_req
