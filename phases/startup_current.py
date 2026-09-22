import numpy as np

from utils.recipe import STARTUP_V, SUPPLY_V


def time_to_pct(t_s, rpm, target_rpm):
    """First sample at or above the target speed."""
    idx = np.where(np.asarray(rpm) >= target_rpm)[0]
    return float(t_s[idx[0]]) if len(idx) else float(t_s[-1])


def startup_current(measurements, bench, pwm_rpm_curve, log):
    """Cold start at 13.2 V, the supply's upper tolerance, both duties
    stepped from 0 to 100 % at once: the tray current recorded whole from
    the supply's digitizer, both tachs alongside. The peak is judged
    against the scaled Intel limit and each rotor against the time it
    takes to reach 90 % of the full speed the previous phase recorded."""
    bench.set_duty("a", 0.0)
    bench.set_duty("b", 0.0)
    bench.supply_off()
    t_s, amps, rpm_a, rpm_b = bench.startup_capture(STARTUP_V)
    bench.supply_on(SUPPLY_V)
    t = np.asarray(t_s)
    peak = float(np.max(amps))
    t90_a = time_to_pct(t, rpm_a, 0.9 * float(pwm_rpm_curve.full_speed_a_rpm))
    t90_b = time_to_pct(t, rpm_b, 0.9 * float(pwm_rpm_curve.full_speed_b_rpm))

    m = measurements.startup
    m.x_axis = t_s
    m.y_axis.current = amps
    m.y_axis.current.aggregations.peak_a = round(peak, 2)
    m.y_axis.rpm_a = rpm_a
    m.y_axis.rpm_a.aggregations.t90_s = round(t90_a, 3)
    m.y_axis.rpm_b = rpm_b
    m.y_axis.rpm_b.aggregations.t90_s = round(t90_b, 3)
    log.info(f"Start at {STARTUP_V} V: peak {peak:.2f} A at {t[int(np.argmax(amps))]:.3f} s, A at 90 % in {t90_a:.2f} s, B in {t90_b:.2f} s over {len(amps)} samples (mock: capture returned without waiting)")
