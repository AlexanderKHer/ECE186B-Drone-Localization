import logging
import time
import csv

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.syncLogger import SyncLogger


# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)

# URI to the Crazyflie to connect to
uri = 'radio://0/80/2M/E7E7E7E7E7'
if __name__ == '__main__':
    # Initialize the low-level drivers (don't list the debug drivers)
    cflib.crtp.init_drivers(enable_debug_driver=False)
    lg_stab = LogConfig(name='stateEstimate', period_in_ms=200)
    lg_stab.add_variable('stateEstimate.x', 'float')
    lg_stab.add_variable('stateEstimate.y', 'float')
    lg_stab.add_variable('stateEstimate.z', 'float')
    # Connect to a Crazyflie
    cf = Crazyflie(rw_cache='./cache')
    with SyncCrazyflie(uri, cf=cf) as scf:
        #start logging
        with SyncLogger(scf, lg_stab) as logger:
            with open('example.csv','a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                # Iterate the logger to get the values
                count = 0
                for log_entry in logger:
                    #print(log_entry[0],log_entry[1],log_entry[2]) #time stamp, data, object name
                    print([log_entry[1]['stateEstimate.x'],log_entry[1]['stateEstimate.y'],log_entry[1]['stateEstimate.z']]) #data
                    # Do useful stuff
                    writer.writerow([log_entry[1].get('stateEstimate.x'),log_entry[1].get('stateEstimate.y'),log_entry[1].get('stateEstimate.z')])
                    count += 1
                    if (count > 10):
                        # The logging will continue until you exit the loop
                        break
                # When leaving this "with" section, the logging is automatically stopped
            # When leaving this "with" section, the connection is automatically closed
