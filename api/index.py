from http.server import BaseHTTPRequestHandler
import json
import numpy as np
from scipy.signal import find_peaks

from backend.adaptive_filter import adaptive_filter
from backend.sqi import compute_sqi, compute_confidence
from backend.hr_analysis import compute_rr, compute_hr, compute_hrv


def detect_r_peaks(signal, fs):
    norm = (signal - np.mean(signal)) / (np.std(signal) + 1e-8)
    enhanced = norm ** 2

    window = int(0.12 * fs)
    enhanced = np.convolve(enhanced, np.ones(window)/window, mode='same')

    threshold = np.mean(enhanced) + 0.5 * np.std(enhanced)
    distance = int(0.4 * fs)

    peaks, _ = find_peaks(enhanced, height=threshold, distance=distance)
    return peaks


class handler(BaseHTTPRequestHandler):

    def _ok(self, payload):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def _err(self, msg, code=500):
        self.send_response(code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": msg}).encode())

    def do_GET(self):
        self._ok({"message": "API WORKING ✅"})

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            data = json.loads(body.decode() if body else "{}")

            signal = np.array(data.get("signal", []), dtype=float)
            fs = int(data.get("fs", 360))

            if signal.size == 0:
                return self._err("Empty signal", 400)

            # 🔥 AUTO FIX SHORT SIGNAL
            if signal.size < fs:
                repeats = int(np.ceil(fs / signal.size))
                signal = np.tile(signal, repeats)[:fs]

            filtered, _ = adaptive_filter(signal, fs)

            sqi, snr = compute_sqi(filtered, fs)
            confidence = compute_confidence(sqi)

            peaks = detect_r_peaks(filtered, fs)
            rr = compute_rr(peaks, fs)

            hr = compute_hr(rr)
            hr = hr[(hr > 40) & (hr < 180)]

            hrv = compute_hrv(rr)

            avg_hr = float(np.mean(hr)) if hr.size else 0.0

            self._ok({
                "avg_hr": avg_hr,
                "snr": float(snr),
                "sqi": float(sqi),
                "confidence": float(confidence),
                "num_beats": int(len(peaks)),
                "hrv": hrv
            })

        except Exception as e:
            self._err(str(e))