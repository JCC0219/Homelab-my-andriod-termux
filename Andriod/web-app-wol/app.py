import json
import os
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

# ================= 配置区域 =================
PORT = 8888
BROADCAST_IP = "255.255.255.255"
DATA_FILE = "devices.json"
HTML_FILE = os.path.join("templates", "index.html")
# ============================================


# 读取设备列表
def load_devices():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


# 保存设备列表
def save_devices(devices):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(devices, f, ensure_ascii=False, indent=2)


# 发送 WOL 魔术包
def send_wol(mac, broadcast=BROADCAST_IP):
    clean_mac = mac.replace(":", "").replace("-", "").replace(" ", "")
    mac_bytes = bytes.fromhex(clean_mac)
    packet = b"\xff" * 6 + mac_bytes * 16
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(packet, (broadcast, 9))


class WOLServer(BaseHTTPRequestHandler):

    def _send_json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        # 根路由：直接读取并返回 templates/index.html 文件
        if self.path == "/":
            if os.path.exists(HTML_FILE):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                with open(HTML_FILE, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"404: templates/index.html not found")
        elif self.path == "/api/devices":
            self._send_json(load_devices())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        data = json.loads(body.decode("utf-8")) if body else {}

        if self.path == "/api/devices":
            devices = load_devices()
            devices.append({"name": data.get("name"), "mac": data.get("mac")})
            save_devices(devices)
            self._send_json({"status": "ok"})

        elif self.path == "/api/wake":
            mac = data.get("mac")
            if not mac:
                return self._send_json(
                    {"status": "error", "message": "缺少 MAC 地址"}, 400
                )
            try:
                send_wol(mac)
                self._send_json({"status": "ok"})
            except Exception as e:
                self._send_json({"status": "error", "message": str(e)}, 500)

    def do_DELETE(self):
        if self.path.startswith("/api/devices"):
            query = parse_qs(urlparse(self.path).query)
            index = int(query.get("index", [-1])[0])

            devices = load_devices()
            if 0 <= index < len(devices):
                devices.pop(index)
                save_devices(devices)
                self._send_json({"status": "ok"})
            else:
                self._send_json(
                    {"status": "error", "message": "无效的设备索引"}, 400
                )


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), WOLServer)
    print(f"🚀 WOL 管理面板启动成功: http://0.0.0.0:{PORT}")
    server.serve_forever()