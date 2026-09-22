"""End-of-line recipe for a dual-rotor 80 mm 12 V hot-swap server fan tray:
the stimulus at every step and the limit each result is judged on.

Limits come from the Intel "4-Wire Pulse Width Modulation (PWM) Controlled
Fans" specification rev 1.2 where it gives a number (PWM frequency window,
RPM within 10 % of the nominal curve, minimum speed at or below 30 % of
maximum, two tach pulses per revolution, start-up current at 13.2 V), from
the vendor's own end-of-line datasheet items (insulation resistance and
dielectric strength, airflow, static pressure, sound pressure at 1 m), and
from ISO 7779 / ECMA-74 for the acoustic method. Where a number is this
line's derivation (the start-up current scaled to a 4 A rotor, the spin-up
time, the rotor mismatch, the airflow tolerance, the vibration limits) it is
marked as such in procedure.yaml."""

# Unit under test: two counter-rotating 80 mm rotors (80 x 80 x 80 mm stack) in one sled,
# 4-wire PWM per rotor, tach at 2 pulses per revolution, one 12 V feed.
SUPPLY_V = 12.0
STARTUP_V = 13.2  # Intel 4.4: start-up current is measured at the upper supply tolerance
ROTORS = ("a", "b")  # a = inlet rotor, b = outlet rotor
NOMINAL_MAX_RPM = {"a": 16000.0, "b": 14500.0}  # tray datasheet, 100 % duty at 12 V
RATED_CURRENT_A = {"a": 4.0, "b": 3.7}  # tray datasheet, 100 % duty at 12 V
CURRENT_MAX_A = {"a": 4.4, "b": 4.1}  # datasheet maximum, rated plus 10 %
BLADES = 7
FRU_IDENTITY = {"part_number": "FT-2U-80CR-12", "hw_rev": "B2", "airflow": "front-to-back", "fru_format": "ipmi-1.0"}

# Insulation and dielectric (vendor EOL items), lines tied together against the sled
IR_TEST_VDC = 500.0
IR_MIN_MOHM = 10.0
DIELECTRIC_VAC = 500.0
DIELECTRIC_DWELL_S = 60.0  # mock returns without waiting
DIELECTRIC_MAX_MA = 5.0

# PWM to RPM curve (Intel 2.1.3 and 2.1.4): duty points and the nominal curve
# as a fraction of the 100 % speed, from the tray datasheet
PWM_FREQ_KHZ = 25.0  # Intel 2.1.2: target 25 kHz, acceptable 21 to 28
DUTY_POINTS_PCT = [20, 30, 50, 70, 100]
NOMINAL_RPM_FRACTION = {20: 0.26, 30: 0.36, 50: 0.56, 70: 0.77, 100: 1.00}
RPM_TOLERANCE_PCT = 10.0  # Intel 2.1.4: within 10 % of the nominal curve at every point
MIN_SPEED_MAX_PCT = 30.0  # Intel 2.1.3: speed at minimum duty at or below 30 % of maximum
ROTOR_MISMATCH_MAX_PCT = 5.0  # this line's derivation, see procedure.yaml
SETTLE_S = 2.0  # per duty point before the tach is read (mock: instant)

# Start-up (Intel 4.4): 0 to 100 % duty step at 13.2 V, current and both tachs captured
STARTUP_CAPTURE_S = 3.5
STARTUP_SAMPLE_HZ = 500.0
STARTUP_PEAK_MAX_A = 2.0 * sum(RATED_CURRENT_A.values())  # 15.4 A, Intel's 2 A scaled, see procedure.yaml
SPIN_UP_MAX_S = 3.0  # time to 90 % of this tray's own full speed, this line's derivation

# Tach integrity (Intel 2.2): two pulses per revolution against the fixture's optical tach
TACH_CHECK_DUTY_PCT = 50
TACH_PULSES_PER_REV = 2
TACH_DUTY_WINDOW_PCT = (40.0, 60.0)
PWM_FREQ_WINDOW_KHZ = (21.0, 28.0)

# Airflow and static pressure on the AMCA 210 / ISO 5801 chamber at 100 % duty
DATASHEET_MAX_AIRFLOW_CFM = 175.0
DATASHEET_MAX_STATIC_PA = 900.0
AIRFLOW_TOLERANCE_PCT = 10.0  # this line's derivation: the datasheet's speed tolerance applied to flow
DAMPER_POINTS = 7  # from free air to shut-off
CHASSIS_DESIGN_CFM = 100.0  # the 2U chassis at full load
CHASSIS_MIN_PA_AT_DESIGN_CFM = 450.0  # this line's derivation from the chassis impedance

# Vibration on the sled at 100 % duty and sound pressure at 1 m (ISO 7779)
VIB_SAMPLE_HZ = 20000.0
VIB_CAPTURE_S = 0.5
VIB_SPECTRUM_MAX_HZ = 5000.0
BEARING_BALLS = 7
BEARING_D_RATIO = 0.32  # ball diameter over pitch diameter, zero contact angle
ONE_X_MAX_G = 1.0  # ISO 21940-11 grade G6.3 at 16 000 rpm, this line's derivation
BEARING_MAX_G = 0.15  # this line's derivation
SPL_MAX_DBA = 74.0  # datasheet 71 dBA plus 3 dB, this line's derivation


def bearing_defect_frequencies(f_r):
    """Ball-pass frequencies of the outer and inner race for one rotor at
    shaft frequency f_r, from the bearing geometry above."""
    n = BEARING_BALLS
    return {
        "bpfo": n / 2.0 * f_r * (1.0 - BEARING_D_RATIO),
        "bpfi": n / 2.0 * f_r * (1.0 + BEARING_D_RATIO),
    }
