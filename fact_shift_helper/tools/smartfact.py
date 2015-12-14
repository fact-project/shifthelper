# -*- encoding:utf-8 -*-
from __future__ import print_function, absolute_import
from collections import defaultdict
import time 
import random
from datetime import datetime
import requests
import inspect

smartfacturl = "http://fact-project.org/smartfact/data/"

class TableCrawler(object):
	connection_error_counter = defaultdict(int)

	def __init__(self, url):
		self._request_web_page(url)
		self._build_page_payload()

	def __getitem__(self,index):
		row, col = index
		return self.page_payload[row].split()[col]

	def _request_web_page(self, url):
		while True:
			try:
				self.web_page = requests.get(url, timeout=15.)
			except requests.exceptions.ConnectionError:
				self.connection_error_counter[url] += 1
				if self.connection_error_counter[url] >= 10:
					raise
				else:
					# sleep between 1 and 2 seconds.
					time.sleep(1. + random.random())
			else:
				self.connection_error_counter[url]=0
				break

	def _build_page_payload(self):
		self.page_payload = self.web_page.text.split('\n')

def str2float(text):
	try:
		number = float(text)
	except:
		number = nan

	return number

def smartfact_time2datetime(fact_time_stamp):
	return datetime.utcfromtimestamp(
		str2float(fact_time_stamp)/1000.0
	)

class SmartFact(object):

	def __init__(self):
		self.status = status
		self.drive = drive
		self.sqm = sqm
		self.sun = sun
		self.weather = weather
		self.currents = currents
		self.container_temperature = container_temperature
		self.current_source = current_source
		self.camera_climate = camera_climate

	def all(self):
		functions = inspect.getmembers(self, predicate=inspect.isfunction)

		full = dict()
		for function in functions:
			full[function[0]] = function[1]()
			
		return full


def drive(url=smartfacturl + 'tracking.data'):
	tc = TableCrawler(url)
	return {
		'Time_Stamp': smartfact_time2datetime(tc[0,0]),
		'Source_Name': tc[1,1:],
		'Right_Ascention_in_h': str2float(tc[2,1]),
		'Declination_in_Deg': str2float(tc[3,1]),
		'Zenith_Distance_in_Deg': str2float(tc[4,1]),
		'Azimuth_in_Deg': str2float(tc[5,1]),
		'Control_Deviation_in_ArcSec': str2float(tc[6,1]),
		'Distance_to_Moon_in_Deg': tc[7,1],	
	}

def sqm(url=smartfacturl + 'sqm.data'):
	tc = TableCrawler(url)
	return {
		'Time_Stamp': smartfact_time2datetime(tc[0,0]),
		'Magnitude': str2float(tc[1,1]),
		'Sensor_Frequency_in_Hz': str2float(tc[2,1]),
		'Sensor_Period_in_s': str2float(tc[4,1]),
		'Sensor_Temperature_in_C': str2float(tc[5,1]),
	}

def sun(url=smartfacturl + 'sun.data'):

	def hhmm2ms(hhmm):
		return int(hhmm[0:2])*3600*1000 + int(hhmm[3:5])*60*1000

	tc = TableCrawler(url)
	time_stamp = smartfact_time2datetime(tc[0,0])
	date_stamp = time_stamp.date()
	date_ms = str2float(tc[0,0])-time_stamp.hour*3600*1000-time_stamp.minute*60*1000-time_stamp.second*1000
	next_day_ms = 24*3600*1000
	return {
		'Time_Stamp': time_stamp,
		'End_of_dark_time':         smartfact_time2datetime(date_ms+next_day_ms+hhmm2ms(tc[1,1])),
		'End_of_astro_twilight':    smartfact_time2datetime(date_ms+next_day_ms+hhmm2ms(tc[2,1])),
		'End_of_nautic_twilight':   smartfact_time2datetime(date_ms+next_day_ms+hhmm2ms(tc[3,1])),
		'Start_of_day_time':        smartfact_time2datetime(date_ms+next_day_ms+hhmm2ms(tc[4,1])),
		'End_of_day_time':          smartfact_time2datetime(date_ms+hhmm2ms(tc[5,1])),
		'Start_of_nautic_twilight': smartfact_time2datetime(date_ms+hhmm2ms(tc[6,1])),
		'Start_of_astro_twilight':  smartfact_time2datetime(date_ms+hhmm2ms(tc[7,1])),
		'Start_of_dark_time':       smartfact_time2datetime(date_ms+hhmm2ms(tc[8,1])),
	}

def weather(url=smartfacturl + 'weather.data'):
	tc = TableCrawler(url)
	return {
		'Time_Stamp': smartfact_time2datetime(tc[0,0]),
		'Sun_in_Percent': tc[1,1:],
		'Moon_in_Percent': tc[2,1:],
		'Temperature_in_C': str2float(tc[3,1]),
		'Dew_point_in_C': str2float(tc[4,1]),
		'Humidity_in_Percent': str2float(tc[5,1]),
		'Pressure_in_hPa': str2float(tc[6,1]),
		'Wind_speed_in_km_per_h': str2float(tc[7,1]),
		'Wind_gusts_in_km_per_h': str2float(tc[8,1]),
		'Wind_direction': tc[9,1:],
		'Dust_TNG_in_ug_per_m3': str2float(tc[10,1]),
	}

def currents(url=smartfacturl + 'current.data'):
	tc = TableCrawler(url)
	return {
		'Time_Stamp': smartfact_time2datetime(tc[0,0]),
		'Clibrated': tc[1,1],
		'Min_current_per_GAPD_in_uA': str2float(tc[2,1]),
		'Med_current_per_GAPD_in_uA': str2float(tc[3,1]),
		'Avg_current_per_GAPD_in_uA': str2float(tc[4,1]),
		'Max_current_per_GAPD_in_uA': str2float(tc[5,1]),
		'Power_camera_GAPD_in_W': str2float(tc[6,1][:-1]), #The W is stucked to the float and needs to be removed
	}

def status(url=smartfacturl + 'status.data'):
	tc = TableCrawler(url)
	return {
		'Time_Stamp': smartfact_time2datetime(tc[0,0]),
		'DIM': tc[1,1:],
		'Dim_Control': tc[2,1:],
		'MCP': tc[3,1:],
		'Datalogger': tc[4,1:],
		'Drive_control': tc[5,1:],
		'Drive_PC_time_check': tc[6,1:],
		'FAD_control': tc[7,1:],
		'FTM_control': tc[8,1:],
		'Bias_control': tc[9,1:],
		'Feedback': tc[10,1:],
		'Rate_control': tc[11,1:],
		'FSC_control': tc[12,1:],
		'GPS_control': tc[13,1:],
		'SQM_control': tc[14,1:],
		'Agilent_control_24V': tc[15,1:],
		'Agilent_control_50V': tc[16,1:],
		'Agilent_control_80V': tc[17,1:],
		'Power_control': tc[18,1:],
		'Lid_control': tc[19,1:],
		'Ratescan': tc[20,1:],
		'Magic_Weather': tc[21,1:],
		'TNG_Weather': tc[22,1:],
		'Magic_Lidar': tc[23,1:],
		'Temperature': tc[24,1:],
		'Chat_server': tc[25,1:],
		'Skype_client': tc[26,1:],
		'Free_disk_space_in_TB': str2float(tc[27,1]),
		'Smartfact_runtime': tc[28,1:],
	}	

def container_temperature(url=smartfacturl + 'temperature.data'):
	tc = TableCrawler(url)
	return {
		'Time_Stamp': smartfact_time2datetime(tc[0,0]),
		'24h_min_temperature_in_C': tc[1,1],
		'Current_temperature_in_C': tc[2,1],
		'24h_max_temperature_in_C': tc[3,1],
	}

def current_source(url=smartfacturl + 'source.data'):
	tc = TableCrawler(url)
	return {
		'Time_Stamp': smartfact_time2datetime(tc[0,0]),
		'Source_Name': tc[1,1:],
		'Right_Ascention_in_h': str2float(tc[2,1]),
		'Declination_in_Deg': str2float(tc[3,1]),
		'Wobble_offset_in_Deg': str2float(tc[4,1]),
		'Wobble_angle_in_Deg': str2float(tc[5,1]),
	}

def camera_climate(url=smartfacturl + 'fsc.data'):
	tc = TableCrawler(url)
	return {
		'Time_Stamp': smartfact_time2datetime(tc[0,0]),
		'Avg_humidity_in_percent': str2float(tc[1,1]),
		'Max_rel_temp_in_C': str2float(tc[2,1]),
		'Avg_rel_temp_in_C': str2float(tc[3,1]),
		'Min_rel_temp_in_C': str2float(tc[4,1]),
	}