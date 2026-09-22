"""Fan tray EOL bench (mock): 12 V programmable supply with current sense,
PWM generator and tach counters for both rotors, the fixture's optical
tach, an IEPE accelerometer on the sled through a DAQ, a class 1 sound
level meter at 1 m, the electrical safety analyzer, and the I2C link to
the tray's FRU EEPROM through the hot-swap connector. One plug because
every reading depends on the duty and the supply voltage at that instant.

Maps to a Keysight N6700C mainframe with an N6754A module (60 V, 20 A) for
the supply and its current digitizer, an NI USB-6363 for the two PWM
counter outputs, the three tach counter inputs and the IEPE analog input
(PCB 352C33 accelerometer through a PCB 482C05 conditioner), a Monarch ROS
optical sensor on a reflective mark on each hub, an NTi Audio XL2 with an
M2230 microphone, and a Chroma 19032 for insulation resistance and the AC
dielectric test. The mock synthesizes a healthy tray: both rotors on their
nominal curve within 2 %, a spin-up that peaks near 12 A at
13.2 V, clean tachs, a balanced rotor pair with new bearings, 70.8 dBA.
The 60 s dielectric dwell and the settling at each duty point return
without waiting. Swap for classes speaking SCPI, nidaqmx and smbus; the
phases stay unchanged.
"""

import math

import numpy as np

from utils.recipe import (
    BLADES,
    FRU_IDENTITY,
    NOMINAL_MAX_RPM,
    NOMINAL_RPM_FRACTION,
    PWM_FREQ_KHZ,
    RATED_CURRENT_A,
    STARTUP_CAPTURE_S,
    STARTUP_SAMPLE_HZ,
    SUPPLY_V,
    VIB_CAPTURE_S,
    VIB_SAMPLE_HZ,
    bearing_defect_frequencies,
)

# This tray's rotors against their nominal curve: the inlet rotor runs
# 1.2 % fast, the outlet rotor 0.6 % slow, and both clamp a little high at
# the 20 % minimum-speed point.
_SPEED_OFFSET = {"a": 0.012, "b": -0.006}
_MIN_DUTY_BIAS = 0.004
_IDLE_CURRENT_A = 0.15
_SPIN_UP_TAU_S = {"a": 0.60, "b": 0.75}
_START_CURRENT_LIMIT_X = 2.0  # the drive's current limit, in multiples of rated, until back-EMF builds
_ONE_X_G = {"a": 0.42, "b": 0.34}
_BLADE_PASS_G = {"a": 0.20, "b": 0.16}
_BEARING_G = {"a": (0.045, 0.030), "b": (0.038, 0.026)}  # (bpfo, bpfi)


class FanBench:
    def __init__(self, serial_number):
        self.serial_number = str(serial_number)
        self._rng = np.random.default_rng(8012)
        self._supply_v = 0.0
        self._duty = {"a": 0.0, "b": 0.0}
        self._power_cycles = 0
        self._last_vibration = None
        # self.psu = pyvisa...("USB0::0x2A8D::...::INSTR"); self.daq = nidaqmx...; self.slm = ...; self.hipot = ...
        print(f"Fan bench connected: supply off, PWM 0 %, tach counters armed for {self.serial_number}")

    # --- supply and PWM -----------------------------------------------------------

    def supply_on(self, volts):
        if self._supply_v == 0.0:
            self._power_cycles += 1
        self._supply_v = float(volts)

    def supply_off(self):
        self._supply_v = 0.0

    def supply_current_a(self):
        if self._supply_v == 0.0:
            return round(abs(self._rng.normal(0.0, 0.001)), 4)
        return round(sum(self._rotor_current_a(r) for r in ("a", "b")), 3)

    def set_duty(self, rotor, pct):
        self._duty[rotor] = float(pct)

    def settle(self, seconds):
        """Wait for the rotor to settle at the new duty (mock: returns at once)."""
        return None

    def power_cycles(self):
        """Supply on/off cycles applied to the tray since the bench was armed."""
        return self._power_cycles

    # --- FRU EEPROM over the hot-swap connector -----------------------------------------

    def fru_identity(self):
        return dict(FRU_IDENTITY)

    def fru_serial(self):
        return self.serial_number

    # --- safety analyzer, supply off ------------------------------------------------------

    def insulation_mohm(self, volts):
        """All lines tied together against the sled at the stated DC voltage."""
        return round(320.0 + self._rng.normal(0.0, 8.0), 1)

    def dielectric_ma(self, volts, dwell_s):
        """AC withstand, lines to sled; leakage in mA at the end of the dwell.
        The mock returns without the 60 s wait."""
        return round(0.18 + abs(self._rng.normal(0.0, 0.01)), 3)

    # --- tachs, optical tach, PWM read-back --------------------------------------------------

    def _rpm(self, rotor):
        duty = self._duty[rotor]
        if self._supply_v == 0.0 or duty <= 0.0:
            return 0.0
        pts = sorted(NOMINAL_RPM_FRACTION)
        frac = float(np.interp(duty, pts, [NOMINAL_RPM_FRACTION[p] for p in pts]))
        if duty <= pts[0]:
            frac += _MIN_DUTY_BIAS
        v_scale = self._supply_v / SUPPLY_V
        return NOMINAL_MAX_RPM[rotor] * frac * (1.0 + _SPEED_OFFSET[rotor]) * v_scale

    def _rotor_current_a(self, rotor):
        ratio = self._rpm(rotor) / NOMINAL_MAX_RPM[rotor]
        return _IDLE_CURRENT_A + (RATED_CURRENT_A[rotor] - _IDLE_CURRENT_A) * ratio**2.5

    def tach_rpm(self, rotor):
        """Speed from the rotor's own tach, counted over one second."""
        return round(self._rpm(rotor) + self._rng.normal(0.0, 12.0), 0)

    def rotor_current_a(self, rotor):
        """Current on the rotor's own feed through the fixture's shunt."""
        return round(self._rotor_current_a(rotor) + self._rng.normal(0.0, 0.01), 3)

    def tach_frequency_hz(self, rotor):
        """Tach pulse frequency from the counter, gated for one second."""
        return round(2.0 * self._rpm(rotor) / 60.0 + self._rng.normal(0.0, 0.3), 2)

    def optical_rpm(self, rotor):
        """True speed from the reflective mark on the hub, one pulse per revolution."""
        return round(self._rpm(rotor) + self._rng.normal(0.0, 4.0), 1)

    def tach_duty_pct(self, rotor):
        return round({"a": 48.6, "b": 51.3}[rotor] + self._rng.normal(0.0, 0.3), 1)

    def pwm_frequency_khz(self, rotor):
        """PWM frequency at the rotor's pins, behind the tray's buffer."""
        return round(PWM_FREQ_KHZ + 0.12 + self._rng.normal(0.0, 0.02), 3)

    # --- start-up capture -----------------------------------------------------------------

    def startup_capture(self, volts):
        """Supply at the stated voltage, both duties stepped 0 to 100 % at
        t = 0, tray current and both tachs sampled together. Time in s,
        current in A, speeds in rpm. Each drive holds its winding at its
        current limit until the rotor's back-EMF builds, so the peak sits
        in the first 200 ms and decays with the spin-up. The mock returns
        the capture without waiting."""
        self.supply_on(volts)
        self.set_duty("a", 100.0)
        self.set_duty("b", 100.0)
        n = int(STARTUP_CAPTURE_S * STARTUP_SAMPLE_HZ)
        t = np.arange(n) / STARTUP_SAMPLE_HZ
        rpm = {}
        current = np.zeros(n)
        for rotor in ("a", "b"):
            tau = _SPIN_UP_TAU_S[rotor]
            full = self._rpm(rotor)
            rpm[rotor] = full * (1.0 - np.exp(-t / tau))
            ratio = rpm[rotor] / NOMINAL_MAX_RPM[rotor]
            steady = _IDLE_CURRENT_A + (RATED_CURRENT_A[rotor] - _IDLE_CURRENT_A) * ratio**2.5
            limited = _START_CURRENT_LIMIT_X * RATED_CURRENT_A[rotor] * (1.0 - np.exp(-t / 0.05)) * np.exp(-t / tau)
            current += steady + limited
        current += self._rng.normal(0.0, 0.03, n)
        for rotor in ("a", "b"):
            rpm[rotor] = rpm[rotor] + self._rng.normal(0.0, 15.0, n)
        return (t.round(3).tolist(), current.round(3).tolist(), rpm["a"].round(0).tolist(), rpm["b"].round(0).tolist())

    # --- accelerometer and microphone -------------------------------------------------------

    def vibration_capture(self):
        """One accelerometer capture on the sled at the present duty, in g
        at 20 kHz. Both rotors contribute their 1x (imbalance), 2x, blade
        pass and the two ball-pass tones of new bearings. The raw capture
        is kept for the teardown to attach."""
        n = int(VIB_SAMPLE_HZ * VIB_CAPTURE_S)
        t = np.arange(n) / VIB_SAMPLE_HZ
        v = self._rng.normal(0.0, 0.02, n)
        for rotor in ("a", "b"):
            f_r = self._rpm(rotor) / 60.0
            d = bearing_defect_frequencies(f_r)
            v += _ONE_X_G[rotor] * np.sin(2 * math.pi * f_r * t + self._rng.uniform(0, 2 * math.pi))
            v += 0.08 * np.sin(2 * math.pi * 2 * f_r * t + self._rng.uniform(0, 2 * math.pi))
            v += _BLADE_PASS_G[rotor] * np.sin(2 * math.pi * BLADES * f_r * t + self._rng.uniform(0, 2 * math.pi))
            v += _BEARING_G[rotor][0] * np.sin(2 * math.pi * d["bpfo"] * t + self._rng.uniform(0, 2 * math.pi))
            v += _BEARING_G[rotor][1] * np.sin(2 * math.pi * d["bpfi"] * t + self._rng.uniform(0, 2 * math.pi))
        samples = v.round(5).tolist()
        self._last_vibration = {"sample_rate_hz": VIB_SAMPLE_HZ, "samples": samples}
        return samples

    def last_vibration_capture(self):
        return self._last_vibration

    def sound_pressure_dba(self):
        """A-weighted sound pressure at 1 m from the inlet on the axis,
        ISO 7779 hemi-anechoic booth, 10 s average."""
        return round(70.8 + self._rng.normal(0.0, 0.15), 1)

    def __del__(self):
        print("PWM 0 %, supply off, bench released")
