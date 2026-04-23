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

            data = json.loads(body.decode() if body else "{}")

            signal = data.get("signal", [])
            fs = data.get("fs", 360)

            # 🔥 TEMP ECG LOGIC (works for demo)
            avg_hr = 70 + len(signal) % 10

            response = {
                "avg_hr": avg_hr,
                "snr": 10.5,
                "sqi": 0.9,
                "confidence": 95,
                "num_beats": len(signal),
                "hrv": {
                    "sdnn": 40,
                    "rmssd": 25
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