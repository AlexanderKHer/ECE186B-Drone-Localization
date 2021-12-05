import logging

from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncLogger import SyncLogger

lg_stab = LogConfig(name='stateEstimate', period_in_ms=10)
lg_stab.add_variable('stateEstimate.x', 'float')
lg_stab.add_variable('stateEstimate.y', 'float')
lg_stab.add_variable('stateEstimate.z', 'float')
log_entry = {}

def getLHPos(scf):
    global log_entry
    with SyncLogger(scf, lg_stab) as logger:
            for log_entry in logger:
                #print(log_entry[0],log_entry[1],log_entry[2]) #time stamp, data, object name
                #print(log_entry[1])
                break

    #print(type(log_entry[1]))
    return [log_entry[1].get('stateEstimate.x',"NULL"),log_entry[1].get('stateEstimate.y',"NULL"),log_entry[1].get('stateEstimate.z',"NULL")]