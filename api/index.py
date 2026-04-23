import json
import numpy as np

from backend.adaptive_filter import adaptive_filter
from backend.sqi import compute_sqi, compute_confidence
from backend.hr_analysis import compute_rr, compute_hr, compute_hrv
from scipy.signal import find_peaks


def detect_r_peaks(signal, fs):
    norm = (signal - np.mean(signal)) / (np.std(signal) + 1e-8)
    enhanced = norm ** 2

    window = int(0.12 * fs)
    enhanced = np.convolve(enhanced, np.ones(window)/window, mode='same')

    threshold = np.mean(enhanced) + 0.5 * np.std(enhanced)
    distance = int(0.4 * fs)

    peaks, _ = find_peaks(enhanced, height=threshold, distance=distance)
    return peaks


def handler(request):
    try:
        # ✅ FIXED parsing (very important)
        body = json.loads(request.body.decode())

        signal = np.array(body.get("signal", []))
        fs = body.get("fs", 360)

        if len(signal) == 0:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Empty signal"})
            }

        filtered, _ = adaptive_filter(signal, fs)

        sqi, snr = compute_sqi(filtered, fs)
        confidence = compute_confidence(sqi)

        peaks = detect_r_peaks(filtered, fs)

        rr = compute_rr(peaks, fs)
        hr = compute_hr(rr)
        hr = hr[(hr > 40) & (hr < 180)]

        hrv = compute_hrv(rr)

        response = {
            "snr": float(snr),
            "sqi": float(sqi),
            "confidence": float(confidence),
            "avg_hr": float(np.mean(hr)) if len(hr) else 0,
            "num_beats": int(len(peaks)),
            "hrv": hrv
        }

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(response)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }