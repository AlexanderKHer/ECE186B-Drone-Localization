import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.position_hl_commander import PositionHlCommander
import LogHelper as LH
import time

# URI to the Crazyflie to connect to
uri = 'radio://0/80/2M/E7E7E7E7E7'

def simple_sequence():
    with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
        with PositionHlCommander(scf, x=0.0, y=0.0, z=0.0, default_velocity=0.1, default_height=0.3) as pc:
            LH.getLHPos(scf)
            pc.back(0.3)
            LH.getLHPos(scf)
            time.sleep(0.5)
            pc.right(0.3)
            LH.getLHPos(scf)
            time.sleep(0.5)
            pc.forward(0.3)
            LH.getLHPos(scf)
            time.sleep(0.5)
            pc.go_to(0.0, 0.0, 0.0)

if __name__ == '__main__':
    cflib.crtp.init_drivers(enable_debug_driver=False)
    simple_sequence()
