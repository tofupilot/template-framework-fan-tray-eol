from utils.recipe import ROTORS, SETTLE_S, SUPPLY_V, TACH_CHECK_DUTY_PCT


def tach_integrity(measurements, bench, log):
    """At 50 % duty, each rotor's tach frequency against the fixture's
    optical tach on the hub: pulses per revolution must be exactly two,
    the tach duty inside the window, and the PWM at the rotor pins, behind
    the tray's buffer, inside the Intel frequency window. A BMC counting
    a one-pulse tach reads the rotor at half speed and drives the whole
    chassis to full speed for nothing."""
    bench.supply_on(SUPPLY_V)
    for r in ROTORS:
        bench.set_duty(r, TACH_CHECK_DUTY_PCT)
    bench.settle(SETTLE_S)
    for r in ROTORS:
        tach_hz = bench.tach_frequency_hz(r)
        optical_rpm = bench.optical_rpm(r)
        pulses = tach_hz * 60.0 / optical_rpm
        duty = bench.tach_duty_pct(r)
        pwm_khz = bench.pwm_frequency_khz(r)
        log.info(f"Rotor {r.upper()}: tach {tach_hz:.1f} Hz, optical {optical_rpm:.0f} rpm, {pulses:.3f} pulses/rev, tach duty {duty:.1f} %, PWM {pwm_khz:.2f} kHz at the pins")
        if r == "a":
            measurements.tach_pulses_per_rev_a = int(round(pulses))
            measurements.tach_duty_a_pct = duty
            measurements.pwm_freq_a_khz = pwm_khz
        else:
            measurements.tach_pulses_per_rev_b = int(round(pulses))
            measurements.tach_duty_b_pct = duty
            measurements.pwm_freq_b_khz = pwm_khz
