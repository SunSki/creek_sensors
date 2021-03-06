
import csv
from datetime import datetime
import json
import statistics
import subprocess
import sys
from time import sleep

import Adafruit_ADS1x15
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import RPi.GPIO as GPIO

# General Setting
SLEEP_TIME = 10 * 60
LOCATION = "test"
CSV_FILE = "data/creek_data.csv"
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# RainSensor Setting
GPIO.setmode(GPIO.BCM)
GPIO.setup(15, GPIO.IN)
RAIN_REPE_NUM = 100
RAIN_REPE_TIME = 0.2

# TemperatureSensor Setting
SENSOR_ID = "28-01191ed4dcbc"
SENSOR_W1_SLAVE = "/sys/bus/w1/devices/" + SENSOR_ID + "/w1_slave"
ERR_VAL = 85000

# DO,pH Setting
ADC = Adafruit_ADS1x15.ADS1115()
GAIN = 1
DOPH_REPE_NUM = 150
DOPH_REPE_TIME = 0.2

PH_MID = 25200
PH_SLOPE_LOW = 1192
PH_INTERCEPT_LOW = 17177
PH_SLOPE_HIGH = 1626
PH_INTERCEPT_HIGH = 14257

DO_SLOPE = 474
DO_INTERCEPT = -1312


def ph_calc(value):
    if value < PH_MID:
        ph = (value - PH_INTERCEPT_LOW) / PH_SLOPE_LOW
    else:
        ph = (value - PH_INTERCEPT_HIGH) / PH_SLOPE_HIGH
    return ph


def do_calc(value):
    do = (value - DO_INTERCEPT) / DO_SLOPE
    return do


def get_rain_state():
    try:
        for _ in range(RAIN_REPE_NUM):
            weather = GPIO.input(15)
            if weather == 0:
                return 'rainy'
            sleep(RAIN_REPE_TIME)
        return 'sunny'
    except:
        return None


def get_temp_value():
    try:
        res = subprocess.check_output(["cat", SENSOR_W1_SLAVE])
        res = res.decode()
        temp_val = res.split("=")
        if temp_val[-1] == ERR_VAL:
            print("Got value:85000. Circuit is ok, but something wrong happens...")
            sys.exit(1)
        temp_val = round(float(temp_val[-1]) / 1000, 1)
        return temp_val
    except:
        return None


def get_DoPh_value():
    for _ in range(DOPH_REPE_NUM):
        do_volt = ADC.read_adc(0, gain=GAIN)
        ph_volt = ADC.read_adc(1, gain=GAIN)
        do_list.append(round(do_volt, -2))
        ph_list.append(round(ph_volt, -2))
        sleep(DOPH_REPE_TIME)

    try:
        do_value = statistics.mode(do_list)
        ph_value = statistics.mode(ph_list)
    except:
        print("No mode")
        do_value = statistics.mean(do_list)
        ph_value = statistics.mean(ph_list)

        return do_value, ph_value
    except:
        return None, None


def get_data():  # weather, temp, do, ph
    print("Start Get data...")
    try:
        weather = get_rain_state()
        print("weather: {}".format(weather))
        temp = get_temp_value()
        print("temp: {}".format(temp))
        do, ph = get_DoPh_value()
        print("do: {}, ph: {}".format(do, ph))
        return weather, temp, do, ph
    except:
        return None


def write_csv(list):
    with open(CSV_FILE, 'a') as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(list)
    print("Finish writing csv")


def write_spreadsheet(data):
    # gspread Setting
    print("Start gspread setting...")
    try:
        SCOPE = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        CREDENTIALS = ServiceAccountCredentials.from_json_keyfile_name(
            '/home/pi/Key/creeks-1574788873145-ecb1ac12ac88.json', SCOPE)
        GC = gspread.authorize(CREDENTIALS)

        SPREADSHEET_KEY = '18jf-W56QqMvjSUgvxBv76Hm3H-HEmgkUZTz-7_Qx1F8'  # 共有設定したスプレッドシートキー
        # 共有設定したスプレッドシートのシート１を開く
        WORKSHEET = GC.open_by_key(SPREADSHEET_KEY).sheet1
        print("Finish gspread setting")
    except:
        print("Error: gspread setting")
        return None

    try:
        index = 1
        while True:
            num = str(index)
            Acell = 'A' + num
            if not WORKSHEET.acell(Acell).value:
                break
            index += 1

        data_num = len(data)
        row_ids = list(LETTERS)
        for i in range(data_num):
            row_id = row_ids[i]
            cell = row_id + num
            WORKSHEET.update_acell(cell, data[i])
        print("Finish writing spreadsheet")
    except:
        print("Error: writing spreadsheet")


def main():
    while True:
        weather, temp, do, ph = get_data()
        dt = datetime.now().strftime('%Y/%m/%d/%H:%M')
        data = [dt, weather, temp, do, ph, LOCATION]

        write_csv(data)
        # write_spreadsheet(data)

        print("Sleep {}s".format(SLEEP_TIME))
        sleep(SLEEP_TIME)


if __name__ == '__main__':
    main()
