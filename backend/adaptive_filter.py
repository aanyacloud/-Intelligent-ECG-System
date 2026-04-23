import numpy as np
from scipy.signal import butter, filtfilt, welch, iirnotch


def butter_bandpass(lowcut, highcut, fs, order=4):
    nyq = 0.5 * fs
    return butter(order, [lowcut / nyq, highcut / nyq], btype='band')


def apply_bandpass(signal, fs):
    b, a = butter_bandpass(0.5, 40, fs)
    return filtfilt(b, a, signal)


def apply_notch(signal, fs, freq=50):
    b, a = iirnotch(freq, Q=30, fs=fs)
    return filtfilt(b, a, signal)


def adaptive_filter(signal, fs):
    # -------- PSD --------
    f, Pxx = welch(signal, fs)
    total_power = np.sum(Pxx) + 1e-8

    # -------- Noise Ratios --------
    low_ratio = np.sum(Pxx[f < 0.5]) / total_power
    power_ratio = np.sum(Pxx[(f > 48) & (f < 52)]) / total_power

    # -------- Dynamic Thresholds (NO hardcoding) --------
    baseline_threshold = np.percentile(Pxx, 75) / total_power
    powerline_threshold = np.percentile(Pxx, 90) / total_power

    filtered = signal.copy()
    steps = []

    # -------- Adaptive Bandpass --------
    if low_ratio > baseline_threshold:
        filtered = apply_bandpass(filtered, fs)
        steps.append("Adaptive Bandpass (Baseline Removed)")
    else:
        steps.append("Baseline Stable (No Removal Needed)")

    # -------- Adaptive Notch --------
    if power_ratio > powerline_threshold:
        filtered = apply_notch(filtered, fs)
        steps.append("Adaptive Notch (Powerline Removed)")
    else:
        steps.append("No Powerline Noise Detected")

    # -------- Normalization (Always Applied) --------
    filtered = (filtered - np.mean(filtered)) / (np.std(filtered) + 1e-8)
    steps.append("Normalization")

    return filtered, steps