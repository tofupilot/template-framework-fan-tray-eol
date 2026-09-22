from utils.recipe import DIELECTRIC_DWELL_S, DIELECTRIC_VAC, IR_TEST_VDC, SUPPLY_V


def identify_and_insulation(measurements, bench, flow_bench, unit, run, log):
    """Setup: the tray is seated on the chamber's inlet plate, the safety
    analyzer tests the lines against the sled with the supply off, then
    the first power-on reads the FRU EEPROM through the hot-swap
    connector. The operator's answers on the latch colour and the grille
    arrive as bound measurements. A tray with a pinched lead under the
    sled, or the wrong airflow variant, stops here before the rotors turn."""
    flow_bench.clamp()
    run.metadata["fixture_matings"] = flow_bench.mating_count()
    bench.supply_off()
    ir = bench.insulation_mohm(IR_TEST_VDC)
    leak = bench.dielectric_ma(DIELECTRIC_VAC, DIELECTRIC_DWELL_S)
    log.info(f"{unit.serial_number}: {ir:.0f} MOhm at {IR_TEST_VDC:.0f} Vdc, {leak:.3f} mA at {DIELECTRIC_VAC:.0f} Vac (mock: the {DIELECTRIC_DWELL_S:.0f} s dwell is not waited)")

    bench.supply_on(SUPPLY_V)
    bench.set_duty("a", 0.0)
    bench.set_duty("b", 0.0)
    fru = bench.fru_identity()
    serial = bench.fru_serial()
    measurements.insulation_mohm = ir
    measurements.dielectric_leakage_ma = leak
    measurements.fru_identity = fru
    measurements.eeprom_serial_matches_label = serial == unit.serial_number
    unit.metadata["hw_rev"] = fru["hw_rev"]
    log.info(f"FRU {fru['part_number']} rev {fru['hw_rev']} {fru['airflow']}, EEPROM serial {serial}, label {unit.serial_number}")
