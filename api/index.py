from http.server import BaseHTTPRequestHandler
import json
import numpy as np
import sys, os

# Fix imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from backend.adaptive_filter import adaptive_filter
from backend.sqi import compute_sqi, compute_confidence
from backend.hr_analysis import compute_rr, compute_hr, compute_hrv


class handler(BaseHTTPRequestHandler):

    def _send(self, data):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            req = json.loads(body.decode() if body else "{}")

            # ✅ Get signal from frontend (NOT hardcoded)
            signal = np.array(req.get("signal", []), dtype=float)
            fs = int(req.get("fs", 360))

            if signal.size == 0:
                return self._send({"error": "No signal provided"})

            # 🔹 Filtering
            filtered, _ = adaptive_filter(signal, fs)

            # 🔹 SQI + SNR
            sqi, snr = compute_sqi(filtered, fs)
            confidence = compute_confidence(sqi)

            # 🔹 Simple peak detection
            peaks = np.arange(0, len(filtered), int(0.4 * fs))

            rr = compute_rr(peaks, fs)
            hr = compute_hr(rr)
            hrv = compute_hrv(rr)

            avg_hr = float(np.mean(hr)) if len(hr) else 0

            self._send({
                "avg_hr": avg_hr,
                "snr": float(snr),
                "sqi": float(sqi),
                "confidence": float(confidence),
                "num_beats": int(len(peaks)),
                "hrv": hrv,
                "signal": filtered.tolist()  # send for graph
            })

        except Exception as e:
            self._send({"error": str(e)})