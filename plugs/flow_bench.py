"""Airflow chamber (mock): an AMCA 210 / ISO 5801 multi-nozzle chamber
whose inlet plate is the tray's fixture, with a motorised damper, the
nozzle differential pressure, the chamber static pressure, and a counter
on the fixture's hot-swap connector. Station scope: the chamber stays
open, the damper stays homed and the mating counter keeps counting from
one tray to the next.

Maps to a Long Win LW-9266-class chamber (or an Airflow Measurement
Systems bench) over its serial protocol. The mock synthesizes this tray's
fan curve: 172 CFM in free air falling to 885 Pa at shut-off. On a real
chamber, each damper point settles for several seconds before the
pressures are read; the mock returns at once.
"""

import numpy as np

_FREE_AIR_CFM = 172.0
_SHUTOFF_PA = 885.0
_CURVE_EXPONENT = 1.8


class FlowBench:
    def __init__(self):
        self._rng = np.random.default_rng(210)
        self._matings = 0
        self._clamped = False
        # self.chamber = serial.Serial("/dev/ttyUSB1", 9600)
        print("Flow chamber ready: damper homed, nozzle bank selected")

    def clamp(self):
        """Seat the tray on the inlet plate and mate the hot-swap connector."""
        self._matings += 1
        self._clamped = True

    def release(self):
        self._clamped = False

    def mating_count(self):
        """Hot-swap connector matings on this fixture since the station started."""
        return self._matings

    def fan_curve(self, points):
        """Damper from fully open to shut, the stated number of points:
        airflow in CFM from the nozzle dP and static pressure in Pa from
        the chamber tap, at the tray's present duty. The mock assumes
        100 % duty."""
        fractions = np.linspace(1.0, 0.0, points)
        cfm = _FREE_AIR_CFM * fractions
        pa = _SHUTOFF_PA * (1.0 - fractions**_CURVE_EXPONENT)
        cfm = cfm + self._rng.normal(0.0, 0.6, points)
        pa = pa + self._rng.normal(0.0, 3.0, points)
        cfm[-1] = 0.0
        return cfm.round(1).tolist(), pa.round(0).tolist()

    def __del__(self):
        print("Damper homed, chamber released")
