import numpy as np
from scipy.signal import find_peaks

def detect_r_peaks(signal, fs):
    # Normalize
    signal = (signal - np.mean(signal)) / (np.std(signal) + 1e-8)

    # Smooth (reduce noise)
    window_size = int(0.08 * fs)
    if window_size > 1:
        signal = np.convolve(signal, np.ones(window_size)/window_size, mode='same')

    # Adaptive threshold
    threshold = np.percentile(signal, 92)

    # Physiological spacing (~350 ms)
    distance = int(0.35 * fs)

    peaks, _ = find_peaks(signal, height=threshold, distance=distance)

    return peaks


# 🔥 ADAPTIVE RR (no hardcoding)
def compute_rr(peaks, fs):
    rr = np.diff(peaks) / fs

    if len(rr) == 0:
        return rr

    median_rr = np.median(rr)

    # adaptive filtering (±30%)
    rr = rr[(rr > 0.7 * median_rr) & (rr < 1.3 * median_rr)]

    return rr


# 🔥 ADAPTIVE HR
def compute_hr(rr):
    if len(rr) == 0:
        return np.array([0])

    hr = 60 / rr
    median_hr = np.median(hr)

    hr = hr[(hr > 0.7 * median_hr) & (hr < 1.3 * median_hr)]

    return hr


def compute_hrv(rr):
    if len(rr) < 2:
        return {"SDNN": 0, "RMSSD": 0}

    diff = np.diff(rr)

    return {
        "SDNN": float(np.std(rr)),
        "RMSSD": float(np.sqrt(np.mean(diff**2)))
    }