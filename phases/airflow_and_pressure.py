import numpy as np

from utils.recipe import CHASSIS_DESIGN_CFM, DAMPER_POINTS, ROTORS, SETTLE_S, SUPPLY_V


def airflow_and_pressure(measurements, bench, flow_bench, log):
    """Both rotors at 100 % on the chamber, the damper walked from fully
    open to shut: airflow from the nozzle bank and static pressure from
    the chamber tap at each point. Free-air flow and shut-off pressure
    are judged against the datasheet, and the curve is interpolated at
    the chassis design flow, the point the server needs. On a real
    chamber each point settles for seconds; the mock returns at once."""
    bench.supply_on(SUPPLY_V)
    for r in ROTORS:
        bench.set_duty(r, 100.0)
    bench.settle(SETTLE_S)
    cfm, pa = flow_bench.fan_curve(DAMPER_POINTS)
    opening = np.linspace(100.0, 0.0, DAMPER_POINTS).round(1).tolist()
    # the curve is sampled with flow decreasing; interp wants it increasing
    at_design = float(np.interp(CHASSIS_DESIGN_CFM, cfm[::-1], pa[::-1]))
    for o, q, p in zip(opening, cfm, pa):
        log.info(f"Damper {o:5.1f} % open: {q:6.1f} CFM at {p:4.0f} Pa")

    m = measurements.fan_curve
    m.x_axis = opening
    m.y_axis.airflow = cfm
    m.y_axis.airflow.aggregations.free_air_cfm = cfm[0]
    m.y_axis.static_pressure = pa
    m.y_axis.static_pressure.aggregations.shutoff_pa = pa[-1]
    m.y_axis.static_pressure.aggregations.at_design_cfm_pa = round(at_design, 0)
    log.info(f"Free air {cfm[0]:.1f} CFM, shut-off {pa[-1]:.0f} Pa, {at_design:.0f} Pa at the chassis design point of {CHASSIS_DESIGN_CFM:.0f} CFM")
