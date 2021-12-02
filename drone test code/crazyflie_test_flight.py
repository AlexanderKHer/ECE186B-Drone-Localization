import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.position_hl_commander import PositionHlCommander
import LogHelper as LH

# URI to the Crazyflie to connect to
uri = 'radio://0/80/2M/E7E7E7E7E7'

def simple_sequence():
    with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
        with PositionHlCommander(
                scf,
                x=0.0, y=0.0, z=0.0,
                default_velocity=0.1,
                default_height=0.1) as pc:
            pc.forward(0.5)
            LH.getLHPos(scf)
            pc.left(0.2)
            #LH.getLHPos(scf)
            pc.right(0.4)
            #LH.getLHPos(scf)
            pc.back(0.7)
            #LH.getLHPos(scf)
            pc.go_to(0.0, 0.0, 0.0)

if __name__ == '__main__':
    cflib.crtp.init_drivers(enable_debug_driver=False)

    simple_sequence()
