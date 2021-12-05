import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.position_hl_commander import PositionHlCommander
import LogHelper as LH
import time
import threading
import numpy as np

# URI to the Crazyflie to connect to
uri = 'radio://0/80/2M/E7E7E7E7E7'

keep_flying = True


def sequence(scf,pc):
    global keep_flying
    pc.go_to(-0.3, 0.3, 0.3)
    for x in np.arange(-0.3,0.4,0.1):
        for y in np.arange(0.3,-0.4,-0.1):
            if(not keep_flying):
                pc.go_to(0.0, 0.0, 0.0)
                return
            #print(round(x,1),round(y,1))
            pc.go_to(round(x,1), round(y,1), 0.3)
            LH.getLHPos(scf)
            time.sleep(0.2)
    pc.go_to(0.0, 0.0, 0.0)
    keep_flying = False
    print("drone done. trying to land")
    pc.land()

def simple_sequence():
    with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
        with PositionHlCommander(scf, x=0.0, y=0.0, z=0.0, default_velocity=0.1, default_height=0.3) as pc:
            global keep_flying
            keep_flying = True
            print("starting move_thread")
            move_thread = threading.Thread(target=sequence, args=(scf,pc,))
            move_thread.start()
            print("doing other stuff")
            time.sleep(15)
            print("done! waiting on thread to finish")
            time.sleep(40)
            print("ending things early!")
            keep_flying = False
            move_thread.join()

            
if __name__ == '__main__':
    cflib.crtp.init_drivers(enable_debug_driver=False)
    simple_sequence()
