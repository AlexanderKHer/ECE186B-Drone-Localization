#!/usr/bin/env python3

import argparse
import logging
import numpy as np
from threading import Event

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.mem import LighthouseBsGeometry
from cflib.crazyflie.mem import LighthouseMemHelper
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.localization import LighthouseBsGeoEstimator
from cflib.localization import LighthouseSweepAngleAverageReader


class Estimator:
    def __init__(self):
        self.sensor_vectors_all = None
        self.collection_event = Event()
        self.write_event = Event()

    def angles_collected_cb(self, angles):
        self.sensor_vectors_all = angles
        self.collection_event.set()

    def estimate(self, uri):
        cf = Crazyflie(rw_cache='./cache')
        with SyncCrazyflie(uri, cf=cf) as scf:
            print("Reading sensor data...")
            sweep_angle_reader = LighthouseSweepAngleAverageReader(scf.cf, self.angles_collected_cb)
            sweep_angle_reader.start_angle_collection()
            self.collection_event.wait()

            print("Estimating position of base stations...")
            geometries = {}
            estimator = LighthouseBsGeoEstimator()
            for id in sorted(self.sensor_vectors_all.keys()):
                average_data = self.sensor_vectors_all[id]
                sensor_data = average_data[1]
                rotation_bs_matrix, position_bs_vector = estimator.estimate_geometry(sensor_data)
                is_valid = estimator.sanity_check_result(position_bs_vector)
                if is_valid:
                    geo = LighthouseBsGeometry()
                    geo.rotation_matrix = rotation_bs_matrix
                    geo.origin = position_bs_vector
                    geo.valid = True

                    geometries[id] = geo

                    self.print_geo(rotation_bs_matrix, position_bs_vector, is_valid)
                else:
                    print("Warning: could not find valid solution for " + id + 1)

                print()

    def print_geo(self, rotation_cf, position_cf, is_valid):
        
        print('python-format')
        print('geo = LighthouseBsGeometry()')
        print('geo.origin =', np.array2string(position_cf, separator=','))
        print('geo.rotation_matrix = [', end='')
        for row in rotation_cf:
            print(np.array2string(row, separator=','), end='')
            print(', ', end='')
        print(']')
        print('geo.valid =', is_valid)


parser = argparse.ArgumentParser()
uri = "radio://0/80/2M"
parser.add_argument("--uri", help="Crazyflie uri. Default: " + uri)
args = parser.parse_args()
if args.uri:
    uri = args.uri

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)
cflib.crtp.init_drivers(enable_debug_driver=False)

estimator = Estimator()
estimator.estimate(uri)