__author__ = 'Todd.Hay'

# -------------------------------------------------------------------------------
# Name:        BcsReader
# Purpose:
#
# Author:      Todd.Hay
# Email:       Todd.Hay@noaa.gov
#
# Created:     Mar 13, 2015
# License:     New BSD
# -------------------------------------------------------------------------------
"""
This BcsReader class is used to get and parse the Bottom Contact Sensor (BCS) data. Note that
there are two versions of the BCS:

- AFSC BCS - This contains a single degree of freedom of tilt, with values from 0 to 90 degrees
             Values outside of this range are considered ???? invalid ????
- NWFSC/FRAM BCS - This contains two degrees of freedom, and X and a Y tilt.  The angles
             range from -180 to 180 degrees, but are reported as 0 > 360 degrees.  The
             NWFSC BCS can store 1MB of data on the datalogger. Given that there are 6 bytes
             of data per reading (3 for each angle), this yields about 44,000 readings
             for a full BCS data logger, which, collected at 1Hz, is about 12 hours of data
"""
import logging
import os
import re
from dateutil import parser, tz
from datetime import timedelta, datetime, timezone
import time
import serial
import csv
import math
from threading import Thread
import arrow
# from pyCollector.Utilities import TimeConverter
# from kivy.event import EventDispatcher
# from kivy.logger import Logger

BUFFER_LIMIT = 10000000


# class BcsReader(EventDispatcher):
class BcsReader:

    """
    Input parameters include:
    filename:  name of the file to reader if file-based, None if otherwise
    raw_contents: text of the raw contents from a database
    bcs_type:  old / new - specifying from the database whether the text is old style (AFSC) or new style (NWFSC)

    """
    def __init__(self, filename=None, raw_content=None, bcs_type=None, serial_stream=False, position='', **kwargs):
        super(BcsReader, self).__init__(**kwargs)

        # TODO Todd Hay - Fix to send signals out
        # self.register_event_type("on_read_buffer")
        # self.register_event_type("on_byte_counter")

        # self.tc = TimeConverter()
        self.filename = filename
        self.content_list = []
        self.position = position
        self.raw_content = raw_content
        self.priority_count = 1

        self.is_streaming = False


        if raw_content:
            # Raw Content given, should be from the database
            format = 'database'

        elif self.filename:
            # Filename given, must open to retrieve the content
            self.raw_content = self.load_from_file()
            format = 'file'

        elif serial_stream:
            # Serial stream, open serial connection to get the content
            # self.raw_content = self.request_data_from_serial()
            format = 'serial'

        if self.raw_content is None:
            # try:
            # 	raise Exception('Invalid file type')
            # except Exception as ex:
            # 	print('exception:', ex)
            # 	return
            # TODO What is the proper way to return from the init and close out the file
            return

        self.sensor_type = self.validate_sensor_type()
        self.content_list = self.get_contents_as_list(format=format)

    @staticmethod
    def on_read_buffer(*args):
        pass

    @staticmethod
    def on_byte_counter(*args):
        pass

    def set_raw_content(self, raw_content=None, position=''):
        """
        Method to reset the raw_content and continue the parsing. This is typically used during a database
        query operation when possibly multiple BCS files are retrieved from the database
        :param raw_content:
        :return:
        """
        if not raw_content:
            return

        self.raw_content = raw_content
        format = 'database'
        self.position = position
        self.sensor_type = self.validate_sensor_type()
        self.content_list = self.get_contents_as_list(format=format)

    def validate_sensor_type(self):
        """
        Method to check whether the BCS data is from an AFSC-designed sensor of a NWFSC-designed sensor
        :param contents:
        :return:
        """

        # base, ext = os.path.splitext(self.filename)
        # ext = ext.strip('.')
        # if ext == 'hobo':
        # 	return None

        # try:
        # 	ascii = self.raw_content.decode('ascii')
        # except:
        # 	return None

        try:
            # Check for NWFSC file type - raw file
            if re.search('H\d{1,3}\s?L\d{5}', self.raw_content) and \
                re.search('FF\d+FF', self.raw_content): # and \
                # re.search('EE\d+EEZ{0,2}$', self.raw_content):

            # if len(self.content_list) == 2 and \
            # 	re.match('^H\d{1,3}\s?L\d{5}', self.content_list[0]) and \
            # 	re.match('^FF\d+FF', self.content_list[1]) and \
            # 	re.search('EE\d+EEZ{0,2}$', self.content_list[1]):
                # TODO Could add another check to check the data size v. count and these should equal

                return 'nwfsc_txt'

            # Check for NWFSC file type - csv formatted file
            if 'xangle' in self.raw_content.lower() and \
                'yangle' in self.raw_content.lower() and \
                'bcs' in self.raw_content.lower():

                return 'nwfsc_csv'

            # Check for AFSC file type
            elif 'plot title' in self.raw_content[0:1000].lower() and \
                'bottom' in self.raw_content[0:1000].lower() and \
                'date time' in self.raw_content[0:1000].lower():

            # elif len(self.content_list) > 2 and \
            # 	'plot title' in ''.join([x.lower() for x in self.content_list[0]]) and \
            # 	'bottom' in ''.join([x.lower() for x in self.content_list[0]]) and \
            # 	'date time' in ''.join([x.lower() for x in self.content_list[1]]) and \
            # 	len(self.content_list[1]) == len(self.content_list[2]):

                return 'afsc'

            return None

        except:

            return None

    def open_serial_connection(self, port=30, baudrate=19200, bytesize=serial.EIGHTBITS,
                     parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, xonxoff=False):
        """
        Method to open the serial port connection to the NWFSC BCS shuttle
        :param baudrate:
        :param bytesize:
        :param parity:
        :param stopbits:
        :param xonxoff:
        :return:
        """
        conn = None
        try:
            conn = serial.Serial(port=port, baudrate=baudrate, bytesize=bytesize,
                                parity=parity, stopbits=stopbits, xonxoff=xonxoff)
            return conn
        except Exception as ex:
            if conn:
                conn.close()
            # self.dispatch('on_read_buffer', 'Error opening shuttle connection: ' + str(ex) + '\n\nThe shuttle has probably gone to sleep or needs to be reset.')
            return None

    def request_data_from_serial(self, comport=29, baudrate=19200):
        """
        Method to send a command to the new FRAM BCS to request data to be downloaded
        :param conn: pyserial connection to the shuttle
        :return:
        """
        conn = self.open_serial_connection(port=comport, baudrate=baudrate)
        if not conn:
            return

        self.bcs_serial_thread = Thread(target=self.serial_port_thread, kwargs=dict(conn=conn))
        self.bcs_serial_thread.start()

    def validate_serial_port_download(self, byte_size=None):
        """
        Method to validate that the NWFSC BCS that was downloaded is indeed valid
        :return:
        """
        if self.raw_content is None:

            print('Failed to download the BCS data')
            # self.dispatch('on_read_buffer', 'failure', 'Failure - failed to download the BCS data')

            return

        footer = re.search('EE\d+EEZ{0,2}$', self.raw_content)

        status = False

        try:
            if footer is not None:
                if len(footer.group()) > 27:
                    data_counts = int(footer.group()[22:27])
                    print('Data Counts:', data_counts)
                    print('Stated Byte Size:', byte_size)

                    if data_counts * 6 + 62 == byte_size:
                        self.sensor_type = self.validate_sensor_type()
                        self.content_list = self.get_contents_as_list(format='serial')

                        # self.dispatch('on_read_buffer', 'success', True)
                        print('Success in downloading the data, proceed to upload to DB')

                    else:
                        status = True

                else:
                    status = True

            else:
                status = True


        except Exception as ex:

            # self.dispatch('on_read_buffer', 'failure', 'Error - error validating the BCS data size')
            print('Error validating the BCS final byte size:', ex)

        if status:

            # self.dispatch('on_read_buffer', 'failure', 'Error - error validating the BCS data size')
            print('Error validating the BCS final byte size:', ex)

    def serial_port_thread(self, conn=None):

        buffer = ''
        activate_reading = True

        is_byte_indicator_found = False
        is_header_found = False

        total_bytes = 0
        current_byte_count = -1
        mod_count = 0
        wait_count = 5
        time_delay = 0.050

        start = time.clock()
        end = time.clock()

        is_successful = False

        self.is_streaming = True

        try:
            while True:

                # self.dispatch('on_byte_counter', len(buffer)-16)

                if not self.is_streaming:
                    conn.close()
                    break

                if total_bytes != 0 and current_byte_count >= total_bytes:
                    print('total bytes reached, breaking...')
                    break

                # if current_byte_count == total_bytes:
                    # TODO Should I do this check?  Is it too rigid?

                # Find the byte indicator of the file to get the overall byte count
                if not is_byte_indicator_found:
                    byte_indicator = re.search('H\d{1,3}\s?L\d{5}', buffer)
                    if byte_indicator:
                        print('byte indicator:', byte_indicator.group())
                        total_bytes = self.get_byte_count(byte_string=byte_indicator.group())
                        print('total bytes:', str(total_bytes))
                        is_byte_indicator_found = True
                        # self.dispatch('on_read_buffer', 'byte_indicator', total_bytes)
                        # self.dispatch('on_read_buffer', 'byte_indicator_group', byte_indicator.group())

                if not is_header_found:
                    header = re.search('FF\d+FF', buffer)
                    if header:
                        # self.dispatch('on_read_buffer', 'header', header.group())
                        is_header_found = True

                # footer = re.search('EE\d+EEZ{0,2}$', buffer)
                footer = re.search('EE\d+EEZ{2}', buffer)
                if footer:
                    print('successfully reach end of data, breaking...')
                    print('buffer size:', len(buffer))
                    is_successful = True
                    # self.dispatch('on_read_buffer', 'footer', footer.group())
                    break


                if re.search('ZZ', buffer):

                    # If we find the end of the data stream, then break
                    print('end of data reached, breaking...')
                    print('buffer size:', len(buffer))
                    is_successful = False
                    break

                if math.floor(current_byte_count / 100) > mod_count:
                    # print('byte_count:', current_byte_count, '>',
                    # 	  'buffer size:', len(buffer),
                    # 	  'conn.inWaiting:', conn.inWaiting(),
                    # 	  buffer[current_byte_count-100:current_byte_count])
                    # self.dispatch('on_read_buffer', 'msg', buffer[current_byte_count-100:current_byte_count])

                    mod_count += 1

                if conn.inWaiting() > BUFFER_LIMIT:		# 10 MB file limit
                    print('flushing input')
                    conn.flushInput()

                if activate_reading:
                    conn.flushInput()
                    for i in range(wait_count):

                        # w - wakes up the BCS device (need for it to have a solid green light
                        conn.write('w'.encode())
                        time.sleep(time_delay)
                        if 'OK' in conn.read(conn.inWaiting()).decode('ISO-8859-1'):
                            conn.flushInput()

                            # TODO Reset the time based on the computer clock

                            # t - this returns the current time in the NWFSC BCS shuttle - from here one can enter
                            #      c to change the time or a space to skip changing the time
                            conn.write('t'.encode())
                            time.sleep(time_delay)

                            # c - this enters the change mode for the current time
                            conn.write('c'.encode())
                            time.sleep(time_delay)

                            now = datetime.now()
                            now_date = now.strftime('%m%d%y')
                            now_time = now.strftime('%H%M%S')

                            # update the date in mmddyy format - no return characters needed, it only wants to see 6 numbers
                            conn.write(now_date.encode())
                            time.sleep(time_delay)

                            # update the time in hhmmss format - no return characters needed, it only wants to see 6 numbers
                            conn.write(now_time.encode())
                            time.sleep(time_delay)

                            break

                    # conn.write('t'.encode())
                    # time.sleep(time_delay)
                    # current_time = conn.read(conn.inWaiting()).decode('ISO-8859-1')
                    # print('current time:', current_time)
                    # conn.write(' '.encode())
                    # time.sleep(time_delay)
                    conn.flushInput()
                    conn.write('r'.encode())
                    activate_reading = False

                current_byte_count += conn.inWaiting()
                # print(current_byte_count)

                # current_data = conn.read(conn.inWaiting()).decode('ISO-8859-1')
                # current_data = re.sub(r"[\x01-\x1F\x7F\x80-\x9F]", "", current_data)
                # buffer += current_data
                # TODO Check that we only receive \x10\x130-9EFZ characters

                buffer += conn.read(conn.inWaiting()).decode('ISO-8859-1')

            conn.close()

            print('end of buffer:', buffer[-240:])

        except Exception as ex:

            if "codec can't encode character" in str(ex):
                # self.dispatch('on_read_buffer', 'failure', 'Download interrupted.  Please wait for shuttle to finish attempting to download and then try again.')
                print('Download interrupted.  Please wait for shuttle to finish attempting to download and then try again.')
            else:
                print('Error downloading serial data:', ex)
            conn.close()

        end = time.clock()
        print('Time to download data:', end-start)

        self.raw_content = buffer

        # Call the method to validate that the download was indeed valid
        self.validate_serial_port_download(byte_size=total_bytes)

    def get_byte_count(self, byte_string=''):
        """
        Method to return the byte count from the first line of the NWFSC BCS data file that is formatted as:
        H01 L56412
        :param byte_string:
        :return:
        """
        if byte_string == '':
            return

        byte_count_arr = [int(x.strip('\r\nH ')) if isinstance(int(x.strip('\r\nH ')), int) else None
                              for x in byte_string.split('L')]

        return byte_count_arr[0]*65536 + byte_count_arr[1]

    def set_bcs_time(self):
        """
        Method to reset the time on the NWFSC BCS shuttle
        :return:
        """

    def load_from_file(self):
        """
        Method to load the sensor file from disk.  Used during the SensorFileUploadScreen
        :return:
        """

        if not self.filename:
            return

        if not os.path.exists(self.filename):
            return

        try:
            f = open(self.filename, 'r')
            raw_content = f.read()
            f.close()
        except UnicodeDecodeError as ex:
            # print('Unicode Error:', ex)
            return None
        except Exception as ex:
            print('Exception Error:', ex)
            return None

        return raw_content

    def get_contents_as_list(self, format=None, sensor_type=None):
        """
        Method to convert the raw_content into a list.  The input parameter, format, will be
        :param format: file / database / serial - this defines the format of the input self.raw_content
        :param bcs_type: old / new - whether the format is older style (AFSC BCS) or newer style (NWFSC BCS)
        :return:
        """

        contents = []

        if format == 'file':
            # Data pulled from a file, so check the filename extension to determine if it a csv format or not

            base, ext = os.path.splitext(self.filename)
            if 'csv' in ext:

                reader = csv.reader(self.raw_content.splitlines(), quoting=csv.QUOTE_ALL, quotechar='"', delimiter=',')
                for row in reader:
                    contents.append(row)

            else:
                try:
                    reader = self.raw_content.splitlines()
                    contents = [line.strip('\n') for line in reader if line.strip('\n') != '']
                except AttributeError as ex:
                    return None

        elif format == 'database':
            # Get the format from the database to determine if it is BCS OLD or BCS NEW formatted.  BCS OLD are csv-
            # formatted files whereas BCS NEW are simple text files

            if self.sensor_type == 'afsc' or self.sensor_type == 'nwfsc_csv':

                reader = csv.reader(self.raw_content.splitlines(), quoting=csv.QUOTE_ALL, quotechar='"', delimiter=',')
                for row in reader:
                    contents.append(row)

            elif self.sensor_type == 'nwfsc_txt':

                reader = self.raw_content.splitlines()
                contents = [line.strip('\n') for line in reader if line.strip('\n') != '']

        elif format == 'serial':

            reader = self.raw_content.splitlines()
            contents = [line.strip('\n') for line in reader if line.strip('\n') != '']

        return contents

    def get_raw_content(self):
        """
        Method to return the raw_contents
        :return:
        """
        return self.raw_content

    def get_start_datetime(self):
        """
        Method to return the start datetime of the given file/contents
        :return:
        """
        if self.content_list == []:
            return

        if self.sensor_type is None or self.sensor_type == '':
            return

        if self.sensor_type == 'afsc':

            header = self.content_list[1]
            data = self.content_list[2:len(self.content_list)]

            datetime_col = -1
            for i, item in enumerate(header):
                if 'date time' in item.lower():
                    datetime_col = i
                    tzone = item.split(',')[1].strip()
                    offset_hour = '00:00'
                    if 'gmt' in tzone.lower():
                        offset_hour = tzone.strip('GMT')

                    # TODO Todd Hay - Confirm that I'm getting the correct date in local time zone
                    start_datetime = arrow.get(data[0][datetime_col] + offset_hour)
                    return start_datetime

                    # start_datetime = parser.parse(data[0][datetime_col] + offset_hour)
                    # return self.tc.local_to_utc(local_time=start_datetime)
                    # return self.local_to_utc(local_time=start_datetime)
                else:
                    continue # Keep looking for the date_time column
            logging.error('BcsReader: Did not find start "date_time" column in BCS header.')
            return None

        elif self.sensor_type == 'nwfsc_csv':

            return None

        elif self.sensor_type == 'nwfsc_txt':

            beginning = re.search('FF\d+FF', self.content_list[1]).group().strip('F')
            if beginning:
                if time.daylight:
                    offset_hour = -time.altzone / 3600
                else:
                    offset_hour = -time.timezone / 3600

                start_datetime = beginning[8:10] + '/' + beginning[10:12] + '/' + beginning[12:14] + \
                            ' ' + beginning[14:16] + ':' + beginning[16:18] + ':' + beginning[18:20] + \
                            ' ' + '%02d:00' % offset_hour
                start_datetime = arrow.get(start_datetime)
                return start_datetime

                # start_datetime = parser.parse(start_datetime)
                # return self.tc.local_to_utc(local_time=start_datetime)

        return None

    def get_end_datetime(self):
        """
        Method to return the ending datetime of the data file
        :return:
        """
        if self.content_list == []:
            return

        if self.sensor_type is None or self.sensor_type == '':
            return

        if self.sensor_type == 'afsc':

            header = self.content_list[1]
            data = self.content_list[2:len(self.content_list)]

            datetime_col = -1
            for i, item in enumerate(header):
                if 'date time' in item.lower():
                    datetime_col = i
                    timezone = item.split(',')[1].strip()
                    offset_hour = '00:00'
                    if 'gmt' in timezone.lower():
                        offset_hour = timezone.strip('GMT')

                    end_datetime = arrow.get(data[len(data)-1][datetime_col] + offset_hour)
                    return end_datetime

                    # end_datetime = parser.parse(data[len(data)-1][datetime_col] + offset_hour)
                    # return self.tc.local_to_utc(local_time=end_datetime)
                else:
                    continue  # Keep looking for the date_time column

                Logger.error('BcsReader: Did not find end "date_time" column in BCS header.')
                return None

        elif self.sensor_type == 'nwfsc_csv':

            return None

        elif self.sensor_type == 'nwfsc_txt':

            ending = re.search('EE\d+EEZ{0,2}', self.content_list[1]).group().strip('EZ')
            if ending:
                if time.daylight:
                    offset_hour = -time.altzone / 3600
                else:
                    offset_hour = -time.timezone / 3600
                end_datetime = ending[8:10] + '/' + ending[10:12] + '/' + ending[12:14] + \
                            ' ' + ending[14:16] + ':' + ending[16:18] + ':' + ending[18:20] + \
                            ' ' + '%02d:00' % offset_hour
                end_datetime = arrow.get(end_datetime)
                return end_datetime

                end_datetime = parser.parse(end_datetime)
                # return self.tc.local_to_utc(local_time=end_datetime)

        return None

    def parse_data(self, angles='x'):
        """
        Method to initiate the parsing process.  If first gets the contents of the file, then it checks to determine
        the type of file and passes the contents to the appropriate method based on the file type
        :param angles:  x / xy - whether to return only the x angle or both the x and y angle (for the NWFSC BCS).  If
                just the x angle, it bounds it between -10 <= x <= 100 so it doesn't throw Integrator out of whack when
                displaying it with the AFSC BCS data that has a range of 0 <= x <= 90
        :return:
        """
        if self.content_list == []:
            return

        tilt_values = []

        if self.sensor_type == 'nwfsc_txt':
            tilt_values = self.parse_nwfsc_txt_bcs_data(angles=angles)
        elif self.sensor_type == 'nwfsc_csv':
            tilt_values = []
        elif self.sensor_type == 'afsc':
            tilt_values = self.parse_afsc_bcs_data()
        else:
            print('sensor_type not found:', self.sensor_type)

        # Reformat the tilt_values into the common structure requested by DataParser
        tilt_dict = {
            'priority': self.priority_count,
            'format': 'Degrees',
            'file': self.position,
            'equipment': self.position,
            'data': tilt_values
        }
        self.priority_count += 1

        return self.position, tilt_dict

    def parse_afsc_bcs_data(self):
        """
        Method to parse the contents of the AFSC-provided BCS data stream.  This data uses the Onset Hoboware
        U22-001 data logger capability (http://www.onsetcomp.com/).  The data is converted from a proprietary
        format to a csv file using the Hoboware software. The output CSV file has two columns of data
        consisting of date-time and temperature readings (that are in turn converted to tilt values).
        :param contents:
        :return: tilt_values: N x 2 array of date-time + tilt values
        """
        metadata = self.content_list[0]
        header = self.content_list[1]
        data = self.content_list[2:len(self.content_list)]
        offset_hour = '00:00'

        datetime_col = -1
        temp_col = -1
        voltage_col = -1
        bcs_offset_hack = 0  # hours
        for i, item in enumerate(header):
            if 'date time' in item.lower():
                datetime_col = i
                tzone = item.split(',')[1].strip()
                if 'gmt' in tzone.lower():
                    offset_hour = tzone.strip('GMT')

                    # FIELD-581 Confirm this fix is still required with newest version of Hoboware
                    if offset_hour == '-08:00':
                        offset_hour = '-07:00'
                        logging.info('\t\t\t\tBCS Parsing. Offset hour switched to -07:00 to overcome Hoboware time zone issue')
                        bcs_offset_hack = 1  # hour

            elif 'temp' in item.lower():
                temp_col = i
            elif 'voltage' in item.lower():
                voltage_col = i

        tilt_values = []
        if datetime_col >= 0:
            for row in data:
                # date_time = parser.parse(row[datetime_col] + offset_hour).isoformat()
                #date_time = self.tc.local_to_utc_as_iso(local_time=parser.parse(row[datetime_col] + offset_hour))
                # local_time = parser.parse(row[datetime_col] + offset_hour) + timedelta(hours=bcs_offset_hack)
                # date_time = self.tc.local_to_utc_as_iso(local_time=local_time)
                try:
                    date_time = arrow.get(row[datetime_col] + offset_hour, 'MM/DD/YY hh:mm:ss AZZ').shift(hours=bcs_offset_hack).isoformat()
                except:
                    logging.error(f"BcsReader error parsing date_time: {row[datetime_col]}, {offset_hour}")
                    continue

                if voltage_col >= 0:
                    try:
                        voltage = float(row[voltage_col])
                        angle = self.convert_voltage_to_angle(voltage=voltage)
                    except:
                        continue

                elif temp_col >= 0:
                    try:
                        temp = float(row[temp_col])
                        angle = self.convert_temp_to_angle(temp=temp)
                    except:
                        continue

                else:
                    continue

                if angle is not None:
                    tilt_values.append([date_time, angle])

        return tilt_values

    def convert_voltage_to_angle(self, voltage=None):
        """
        Method to convert voltage readings to angle readings. This was once done when we knew how to
        directly read the Hoboware BCS voltage readings, but apparently Hoboware has change the format
        of the proprietary files such that we don't know how to do this anymore
        :param voltage:
        :return:
        """
        if not voltage:
            return

        try:
            voltage = float(voltage)
        except:
            return

        if voltage <= 0:
            angle = 90
        elif voltage > 0 and voltage <= 1516:
            angle = 90 - 0.02676 * voltage - 0.00006232 * math.pow(voltage, 2)
        elif voltage > 1516 and voltage <= 1530:
            angle = 477.69 - 0.2919 * voltage
        elif voltage > 1530 and voltage <= 2000:
            angle = 130.53 - 0.0650 * voltage
        elif voltage > 2000:
            angle = 0

        return angle

    def convert_temp_to_angle(self, temp=None):
        """
        Method to convert temperature readings to angle readings
        :param temp:
        :return:
        """
        if not temp:
            return

        try:
            temp = float(temp)

        except:
            return

        # if temp < 75 or temp > 300:
        # 	return None

        if temp <= 79:
            angle = 0

        elif temp <= 300:
            angle = -276.4028 + \
                5.728313 * temp + \
                -0.03567424 * math.pow(temp, 2) + \
                0.0001011321 * math.pow(temp, 3) + \
                -0.0000001080326 * math.pow(temp, 4)

        else:
            angle = 87

        return angle

    def parse_nwfsc_txt_bcs_data(self, angles='x'):
        """
        Method to parse the contents of the NWFSC/FRAM BCS data stream.  The ascii data is passed in as the
        contents variable
        :param angles:  x / xy - whether to return only the X or X and Y angles
        :return: tilt_values - N x 3 dimensional array of date-time, X tilt, Y tilt
        """
        # byte_count_arr = [int(x.strip('\r\nH')) if int(x.strip('\r\nH')) else x.strip('\r\nH')
        # 					  for x in self.content_list[0].split(' L')]
        # byte_count = byte_count_arr[0]*65536 + byte_count_arr[1]
        byte_count = self.get_byte_count(byte_string=self.content_list[0])
        # print('Total byte size:', byte_count, 'bytes')

        beginning = re.search('FF\d+FF', self.content_list[1]).group().strip('F')
        ending = re.search('EE\d+EEZ{0,2}', self.content_list[1]).group().strip('EZ')
        count = ending[20:25]
        data = re.search('FF\d+EE', self.content_list[1]).group().strip('FE')

        # print('File Data:')
        # print('\tBeginning:', beginning)
        # print('\tEnding:', ending)
        # print('\tCount:', count)

        if time.daylight:
            offset_hour = -time.altzone / 3600
        else:
            offset_hour = -time.timezone / 3600

        # start_datetime = beginning[8:10] + '/' + beginning[10:12] + '/' + beginning[12:14] + \
        #             ' ' + beginning[14:16] + ':' + beginning[16:18] + ':' + beginning[18:20] + \
        #             ' ' + '%02d:00' % offset_hour
        # self.start_datetime = parser.parse(start_datetime)


        offset_hour = '%02d:00' % offset_hour

        offset_hour = "-07:00"
        self.start_datetime = arrow.get(beginning[8:20] + offset_hour, 'MMDDYYHHmmssZZ')

        # print('\nParsed Results:  (Note: parsed times are in ISO format, UTC time zone (7 hours ahead)')
        # print('\tStart Date-Time:', self.start_datetime.isoformat())


        # TODO Convert 2 angle values into 1 angle between 0 and 90
        # Iterate through the data, turning it into a N x 3 lis
        tilt_values = []
        current_datetime = self.start_datetime
        for values in re.findall(".{6}", data):

            if angles == 'x':

                value = int(values[0:3])

                if 0 <= value < 270:
                    value = 90 - value
                else:
                    value = 450 - value

                # If the value is not between 0 <= x <= 359, then it is a bad value, indicate so
                # TODO

                # else:
                # 	value = 999		# Bad Data

                # Values have been converted between -179 <= x <= 180
                # Set overall boundaries for what will be returned and plotted in Integrator
                if value < -10:
                    value = -10
                elif value > 100:
                    value = 100

                # tilt_values.append([current_datetime.astimezone().isoformat(), value])
                tilt_values.append([current_datetime.isoformat(), value])

            elif angles == 'xy':
                # tilt_values.append([current_datetime.astimezone().isoformat(), int(values[0:3])-180, int(values[3:6])-180])
                tilt_values.append([current_datetime.isoformat(), int(values[0:3])-180, int(values[3:6])-180])

            current_datetime.shift(seconds=1)
            # current_datetime += timedelta(seconds=1)

        # Format:  date-time, X, Y
        # print(tilt_values)
        # print('angle:', angles)
        return tilt_values

if __name__ == '__main__':

    folder = r'..\data\samples'
    filename = r'bcs_new\03_31_14_test.bin'
    # filename = r'bcs_new\03_30_14_test.bin'

    # filename = r'bcs_old\bcs_201403008004p.csv'
    # filename = r'bcs_old\bcs_201403008004s.csv'

    filename = os.path.join(folder, filename)

    # reader = open(file, 'r')
    # contents = reader.readlines()
    # reader.close()

    # bcs_reader = BcsReader(filename=filename)
    # bcs_reader.request_data_from_serial()

    bcs_reader = BcsReader(serial_stream=True)
    bcs_reader.request_data_from_serial()

    start = bcs_reader.get_start_datetime()
    end = bcs_reader.get_end_datetime()
    print(start, ">", end)

    tilt_values = bcs_reader.parse_data(angles='x')
    raw_content = bcs_reader.get_raw_content()
    print('raw content:', raw_content)

    if tilt_values:
        for x in tilt_values:
            print(x)
            pass

        print('\ttilt[0]:', tilt_values[0])
        print('\ttilt[' + str(len(tilt_values)-1), ']:', tilt_values[len(tilt_values)-1])

        print('\ttilt_values count:', len(tilt_values))
