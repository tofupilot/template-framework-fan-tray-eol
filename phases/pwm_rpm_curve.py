import numpy as np

from utils.recipe import DUTY_POINTS_PCT, NOMINAL_MAX_RPM, ROTORS, SETTLE_S, SUPPLY_V


def curve_stats(rotor, rpm, log):
    """Intel 3.3: the speed as a percentage of the rotor's own full speed
    must match the duty within 10 points; 3.2: the 20 % point at or below
    30 % of full speed."""
    pct_of_full = 100.0 * np.array(rpm) / rpm[-1]
    dev = pct_of_full - np.array(DUTY_POINTS_PCT)
    worst = dev[np.argmax(np.abs(dev))]
    log.info(f"Rotor {rotor.upper()}: worst deviation {worst:+.2f} points from the duty line, {pct_of_full[0]:.1f} % of full speed at {DUTY_POINTS_PCT[0]} % duty")
    return round(float(abs(worst)), 2), round(float(pct_of_full[0]), 1)


def pwm_rpm_curve(measurements, bench, log):
    """Both rotors through the duty points at 12 V, speed from each tach
    and current from each feed. Each rotor is judged against the duty line
    (speed in percent of its own full speed within 10 points of the duty,
    the 20 % point at or below 30 %), its full speed against the datasheet,
    and the two rotors against each other at 100 %: a rotor that lags its
    twin is loaded, even inside its own band."""
    bench.supply_on(SUPPLY_V)
    rpm = {r: [] for r in ROTORS}
    amps = {r: [] for r in ROTORS}
    for duty in DUTY_POINTS_PCT:
        for r in ROTORS:
            bench.set_duty(r, duty)
        bench.settle(SETTLE_S)
        for r in ROTORS:
            rpm[r].append(bench.tach_rpm(r))
            amps[r].append(bench.rotor_current_a(r))
        log.info(f"{duty:3d} %: A {rpm['a'][-1]:.0f} rpm {amps['a'][-1]:.2f} A, B {rpm['b'][-1]:.0f} rpm {amps['b'][-1]:.2f} A")

    dev_a, min_a = curve_stats("a", rpm["a"], log)
    dev_b, min_b = curve_stats("b", rpm["b"], log)
    m = measurements.pwm_curve
    m.x_axis = DUTY_POINTS_PCT
    m.y_axis.rpm_a = rpm["a"]
    m.y_axis.rpm_a.aggregations.max_dev_pct = dev_a
    m.y_axis.rpm_a.aggregations.min_speed_pct = min_a
    m.y_axis.rpm_b = rpm["b"]
    m.y_axis.rpm_b.aggregations.max_dev_pct = dev_b
    m.y_axis.rpm_b.aggregations.min_speed_pct = min_b
    m.y_axis.current_a = amps["a"]
    m.y_axis.current_a.aggregations.at_100_pct_a = amps["a"][-1]
    m.y_axis.current_b = amps["b"]
    m.y_axis.current_b.aggregations.at_100_pct_a = amps["b"][-1]

    full_a = rpm["a"][-1]
    full_b = rpm["b"][-1]
    mismatch = 100.0 * abs(full_a / NOMINAL_MAX_RPM["a"] - full_b / NOMINAL_MAX_RPM["b"])
    measurements.full_speed_a_rpm = full_a
    measurements.full_speed_b_rpm = full_b
    measurements.rotor_mismatch_pct = round(mismatch, 2)
    log.info(f"Full speed A {full_a:.0f} rpm, B {full_b:.0f} rpm, normalised mismatch {mismatch:.2f} %")
