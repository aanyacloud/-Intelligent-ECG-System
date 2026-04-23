from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):

    def _set_headers(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        self.wfile.write(json.dumps({
            "message": "API WORKING ✅"
        }).encode())

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

            # decode safely
            data = json.loads(body.decode() if body else "{}")

            signal = data.get("signal", [])
            fs = data.get("fs", 360)

            # 🔥 TEMP DUMMY LOGIC (replace later with your ECG code)
            response = {
                "avg_hr": 72,
                "snr": 12.5,
                "sqi": 0.92,
                "confidence": 95.0,
                "num_beats": len(signal) // 2 if signal else 0,
                "hrv": {
                    "sdnn": 45,
                    "rmssd": 32
                }
            }

            self._set_headers()
            self.wfile.write(json.dumps(response).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()

            self.wfile.write(json.dumps({
                "error": str(e)
            }).encode())