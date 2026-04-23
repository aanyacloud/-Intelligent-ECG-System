import numpy as np
from scipy.signal import welch

def compute_snr(signal, fs):
    f, Pxx = welch(signal, fs)

    signal_power = np.sum(Pxx[(f > 0.5) & (f < 40)])
    noise_power = np.sum(Pxx[(f <= 0.5) | (f >= 40)]) + 1e-8

    return 10 * np.log10(signal_power / noise_power)

def compute_sqi(signal, fs):
    snr = compute_snr(signal, fs)
    variance = np.var(signal)
    mean = np.mean(signal)

    score = (1/(1+np.exp(-snr/10))*0.5 +
             variance/(variance+1)*0.3 +
             1/(1+abs(mean))*0.2) * 100

    return score, snr

def compute_confidence(sqi):
    return (1/(1+np.exp(-(sqi-50)/10))) * 100