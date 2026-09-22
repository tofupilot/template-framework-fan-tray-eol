import numpy as np

from utils.recipe import BLADES, ROTORS, SETTLE_S, VIB_SAMPLE_HZ, VIB_SPECTRUM_MAX_HZ, bearing_defect_frequencies


def peak_near(freqs, spectrum, target_hz, tolerance_bins=3):
    """Largest bin within a few bins of the target, so a speed that drifts
    a few rpm during the capture still lands on the tone."""
    idx = int(np.argmin(np.abs(freqs - target_hz)))
    lo = max(0, idx - tolerance_bins)
    hi = min(len(spectrum), idx + tolerance_bins + 1)
    return float(np.max(spectrum[lo:hi]))


def vibration_and_acoustic(measurements, bench, log):
    """Both rotors at 100 %, one accelerometer capture on the sled, the
    spectrum by FFT. The 1x tone of each rotor, at the shaft frequency
    the tach gives, is the imbalance; the ball-pass tones of each rotor's
    bearing are the bearing check. The blade-pass tone is logged, not
    judged: it is the fan's aerodynamics, not a defect. Then the
    A-weighted sound pressure at 1 m on the inlet axis."""
    bench.settle(SETTLE_S)
    samples = np.asarray(bench.vibration_capture())
    window = np.hanning(len(samples))
    spectrum = np.abs(np.fft.rfft(samples * window)) * 2.0 / np.sum(window)
    freqs = np.fft.rfftfreq(len(samples), 1.0 / VIB_SAMPLE_HZ)
    one_x = {}
    bearing = {}
    for r in ROTORS:
        f_r = bench.tach_rpm(r) / 60.0
        d = bearing_defect_frequencies(f_r)
        one_x[r] = peak_near(freqs, spectrum, f_r)
        bpfo = peak_near(freqs, spectrum, d["bpfo"])
        bpfi = peak_near(freqs, spectrum, d["bpfi"])
        bearing[r] = max(bpfo, bpfi)
        blade = peak_near(freqs, spectrum, BLADES * f_r)
        log.info(f"Rotor {r.upper()} at {f_r * 60:.0f} rpm: 1x {one_x[r]:.3f} g at {f_r:.0f} Hz, BPFO {bpfo:.3f} g at {d['bpfo']:.0f} Hz, BPFI {bpfi:.3f} g at {d['bpfi']:.0f} Hz, blade pass {blade:.3f} g at {BLADES * f_r:.0f} Hz")
    spl = bench.sound_pressure_dba()

    keep = freqs <= VIB_SPECTRUM_MAX_HZ
    m = measurements.spectrum
    m.x_axis = freqs[keep].round(1).tolist()
    m.y_axis.amplitude = spectrum[keep].round(4).tolist()
    m.y_axis.amplitude.aggregations.one_x_a_g = round(one_x["a"], 3)
    m.y_axis.amplitude.aggregations.one_x_b_g = round(one_x["b"], 3)
    m.y_axis.amplitude.aggregations.bearing_a_g = round(bearing["a"], 3)
    m.y_axis.amplitude.aggregations.bearing_b_g = round(bearing["b"], 3)
    measurements.sound_pressure_dba = spl
    log.info(f"{spl:.1f} dBA at 1 m, {int(keep.sum())} bins to {VIB_SPECTRUM_MAX_HZ:.0f} Hz")
