import Adafruit_ADS1x15
import statistics
from time import sleep

# DO,pH Setting
ADC = Adafruit_ADS1x15.ADS1115()
GAIN = 1
DOPH_REPE_NUM = 150
DOPH_REPE_TIME = 0.2


def get_DoPh_value():
    do_list = []
    ph_list = []

    for _ in range(DOPH_REPE_NUM):
        do_volt = ADC.read_adc(0, gain=GAIN)
        ph_volt = ADC.read_adc(1, gain=GAIN)
        do_list.append(round(do_volt, -1))
        ph_list.append(round(ph_volt, -1))
        sleep(DOPH_REPE_TIME)

    try:
        do_value = statistics.mode(do_list)

    except:
        do_value = statistics.mean(do_list)

    try:
        ph_value = statistics.mode(ph_list)
    except:
        ph_value = statistics.mean(ph_list)

    return do_value, ph_value


def main():
    while True:
        print("measuring...")
        do, ph = get_DoPh_value()
        print("do_value:{}, ph_value:{}".format(do, ph))


if __name__ == "__main__":
    main()
