import json
import numpy as np
from http.server import BaseHTTPRequestHandler

# Import your actual backend modules
from backend.adaptive_filter import adaptive_filter
from backend.sqi import compute_sqi, compute_confidence
from backend.hr_analysis import compute_rr, compute_hr, compute_hrv

from scipy.signal import find_peaks

# -------- R-PEAK DETECTION --------
def detect_r_peaks(signal, fs):
    norm = (signal - np.mean(signal)) / (np.std(signal) + 1e-8)
    enhanced = norm ** 2

    window = int(0.12 * fs)
    enhanced = np.convolve(enhanced, np.ones(window)/window, mode='same')

    threshold = np.mean(enhanced) + 0.5 * np.std(enhanced)
    distance = int(0.4 * fs)

    peaks, _ = find_peaks(enhanced, height=threshold, distance=distance)
    return peaks


# -------- VERCEL HANDLER --------
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)

            data = json.loads(body)

            # Input
            signal = np.array(data.get("signal", []))
            fs = data.get("fs", 360)

            if len(signal) == 0:
                raise ValueError("Empty signal")

            # -------- PROCESS PIPELINE --------
            filtered, _ = adaptive_filter(signal, fs)

            sqi, snr = compute_sqi(filtered, fs)
            confidence = compute_confidence(sqi)

            peaks = detect_r_peaks(filtered, fs)

            rr = compute_rr(peaks, fs)
            hr = compute_hr(rr)
            hr = hr[(hr > 40) & (hr < 180)]

            hrv = compute_hrv(rr)

            # -------- RESPONSE --------
            response = {
                "snr": float(snr),
                "sqi": float(sqi),
                "confidence": float(confidence),
                "avg_hr": float(np.mean(hr)) if len(hr) else 0,
                "num_beats": int(len(peaks)),
                "hrv": hrv
            }

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

        except Exception as e:
            self.send_response(400)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())