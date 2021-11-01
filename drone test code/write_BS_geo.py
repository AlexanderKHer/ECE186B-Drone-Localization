import logging
from threading import Event

import cflib.crtp  # noqa
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.mem import LighthouseBsCalibration
from cflib.crazyflie.mem import LighthouseBsGeometry
from cflib.crazyflie.mem import LighthouseMemHelper
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie

import BS_geo_configs

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)

class WriteMem:
    def __init__(self, uri, geo_dict):
        self._event = Event()
        with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
            helper = LighthouseMemHelper(scf.cf)
            helper.write_geos(geo_dict, self._data_written)
            self._event.wait()

    def _data_written(self, success):
        if success:
            print('Data written')
        else:
            print('Write failed')
        self._event.set()

uri = 'radio://0/80'

# Initialize the low-level drivers
cflib.crtp.init_drivers()

# Note: base station ids (channels) are 0-indexed
geo_dict = {0: BS_geo_configs.geo0, 1: BS_geo_configs.geo1}

WriteMem(uri, geo_dict)