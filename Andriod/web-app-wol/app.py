import json
import os
import platform
import socket
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

# ================= 配置区域 =================
PORT = 8888
BROADCAST_IP = "255.255.255.255"
DATA_FILE = "devices.json"
HTML_FILE = os.path.join("templates", "index.html")
# ============================================


def load_devices():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_devices(devices):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(devices, f, ensure_ascii=False, indent=2)


def send_wol(mac, broadcast=BROADCAST_IP):
    clean_mac = mac.replace(":", "").replace("-", "").replace(" ", "")
    mac_bytes = bytes.fromhex(clean_mac)
    packet = b"\xff" * 6 + mac_bytes * 16
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        # ✅ 已修复 soccer -> socket
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(packet, (broadcast, 9))


# 检测 IP 是否在线 (Ping 1 次，超时 1 秒)
def ping_ip(ip):
    param = "-n" if platform.system().lower() == "windows" else "-c"
    timeout_param = "-w" if platform.system().lower() == "windows" else "-W"
    cmd = ["ping", param, "1", timeout_param, "1", ip]
    try:
        res = subprocess.run(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2
        )
        return res.returncode == 0
    except Exception:
        return False


class WOLServer(BaseHTTPRequestHandler):

    def _send_json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/":
            if os.path.exists(HTML_FILE):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                with open(HTML_FILE, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()

        elif parsed.path == "/api/devices":
            self._send_json(load_devices())

        # 检查 Ping 状态接口: /api/ping?ip=192.168.1.100
        elif parsed.path == "/api/ping":
            query = parse_qs(parsed.query)
            ip = query.get("ip", [""])[0]
            if ip:
                is_online = ping_ip(ip)
                self._send_json({"ip": ip, "online": is_online})
            else:
                self._send_json(
                    {"status": "error", "message": "缺少 IP 参数"}, 400
                )
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            return self._send_json({"status": "error", "message": "Invalid JSON"}, 400)

        if self.path == "/api/devices":
            devices = load_devices()
            devices.append(
                {
                    "name": data.get("name"),
                    "ip": data.get("ip"),
                    "mac": data.get("mac"),
                }
            )
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
            try:
                index = int(query.get("index", [-1])[0])
            except ValueError:
                index = -1

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