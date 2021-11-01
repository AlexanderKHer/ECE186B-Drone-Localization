## Copy this file to config.mk and modify to get you personal build configuration

## Weight of the Crazyflie, including decks. The default setting is a Crazyflie 2.X without decks.
CFLAGS += -DCF_MASS=0.0949f

## Brushless handling
# Start disarmed, needs to be armed before being able to fly
# CFLAGS += -DSTART_DISARMED
# IDLE motor drive when armed, 0 = 0%, 65535 = 100% (the motors runs as long as the Crazyflie is armed)
CFLAGS += -DDEFAULT_IDLE_THRUST=5000

## Lighthouse handling
# If lighthouse will need to act as a ground truth (so not entered in the kalman filter)
# CFLAGS += -DLIGHTHOUSE_AS_GROUNDTRUTH
