import logging
import sys
import time
import keyboard

import cflib.crtp # crazie_radio lib
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
import LogHelper as LH


# my vector object
class controller_class:
    def __init__(self): # class constructor
        self.vector_x = 0
        self.vector_y = 0
        self.vector_z = 0
        self.yaw = 0
        self.keep_flying = False
    
    # debug print
    def print_vectors(self):
        print(f'{ self.vector_x},{ self.vector_y},{ self.vector_z}')

# create my vector object
cntr_object = controller_class()


# my keyboard callback function
# gets called anytime there is a keyboard event
# responds to WASD and q and, arrow keys
# requires cntr_object to exist
def key_events_callback(e):
    #for code in keyboard._pressed_events:
    #    print(code)
    k = list(keyboard._pressed_events.keys())
    # press q to unhook keyboard events
    if 16 in k:
        # stop the crazyflie flying
        cntr_object.keep_flying = False
        keyboard.unhook_all()
        
    # up key and not down key    
    if 72 in k and 80 not in k: # forward
        cntr_object.vector_x = 0.5
    elif  80 in k and 72 not in k: # back
        cntr_object.vector_x = -0.5
    else:
        cntr_object.vector_x = 0
    
    # left key and not right key
    if 75 in k and 77 not in k: # left
        cntr_object.vector_y = 0.5
    elif  77 in k and 75 not in k: # right
        cntr_object.vector_y = -0.5
    else:
        cntr_object.vector_y = 0
       
    # 'w' key and not 's' key
    if 17 in k and 31 not in k: #z up
        cntr_object.vector_z = 0.2
    elif  31 in k and 17 not in k: #z down
        cntr_object.vector_z = -0.2
    else:
        cntr_object.vector_z = 0


URI = 'radio://0/80/2M'

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)

if __name__ == '__main__':
    # Initialize the low-level drivers (don't list the debug drivers)
    cflib.crtp.init_drivers(enable_debug_driver=False)

    cf = Crazyflie(rw_cache='./cache')
    with SyncCrazyflie(URI, cf=cf) as scf:
        with MotionCommander(scf) as motion_commander:
                # set true for flight
                cntr_object.keep_flying = True

                keyboard.hook(key_events_callback)

                while cntr_object.keep_flying:
                    motion_commander.start_linear_motion( cntr_object.vector_x, cntr_object.vector_y, cntr_object.vector_z)
                    LH.getLHPos(scf)
                    # send packets at a specific interval
                    time.sleep(0.05)

        print('Control Interface Offline!')
        print('Done')