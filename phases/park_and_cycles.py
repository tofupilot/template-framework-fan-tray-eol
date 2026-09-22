import io

import numpy as np

from utils.recipe import ROTORS


def park_and_cycles(measurements, bench, flow_bench, unit, run, attach, log):
    """Teardown: PWM to 0 on both rotors, supply off, the tray released
    from the chamber plate, whatever happened before. The power cycles
    this test applied go on the unit against its 7 500-cycle budget, the
    fixture's mating count on the run for connector wear, and the raw
    accelerometer capture is attached so a bearing can be re-analysed
    later without the tray."""
    for r in ROTORS:
        bench.set_duty(r, 0.0)
    bench.supply_off()
    residual = bench.supply_current_a()
    flow_bench.release()
    cycles = bench.power_cycles()
    matings = flow_bench.mating_count()
    measurements.current_after_park_a = residual
    measurements.power_cycles_applied = cycles
    unit.metadata["power_cycles"] = cycles
    run.metadata["fixture_matings"] = matings

    raw = bench.last_vibration_capture()
    if raw:
        buf = io.StringIO()
        np.savetxt(buf, np.asarray(raw["samples"]), fmt="%.5f", header=f"acceleration_g at {raw['sample_rate_hz']:.0f} Hz", comments="# ")
        attach.data(buf.getvalue().encode(), "vibration_raw_20khz.csv")
    log.info(f"Parked: {residual:.4f} A with the supply off, {cycles} power cycles applied, fixture mating {matings}, raw capture {'attached' if raw else 'absent'}")
