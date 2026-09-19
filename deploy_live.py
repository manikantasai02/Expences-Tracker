import subprocess
import re
import sys
import os

exe_path = r"C:\Users\sures\AppData\Local\Programs\Python\Python313\Lib\site-packages\pycloudflared\cloudflared-windows-amd64.exe"
if not os.path.exists(exe_path):
    import pycloudflared.util as u
    exe_path = u.get_info().executable

cmd = [exe_path, "tunnel", "--url", "http://127.0.0.1:5000"]

proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, encoding="utf-8")
url_pattern = re.compile(r"(https?://\S+\.trycloudflare\.com)")

tunnel_url = None
for line in proc.stderr:
    match = url_pattern.search(line)
    if match:
        tunnel_url = match.group(1)
        with open("public_url.txt", "w", encoding="utf-8") as f:
            f.write(tunnel_url.strip() + "\n")
        print(f"\n=======================================================")
        print(f" LIVE PUBLIC DEPLOYMENT IS ACTIVE AT:")
        print(f" -> {tunnel_url}")
        print(f"=======================================================\n")
        sys.stdout.flush()
        break

try:
    proc.wait()
except KeyboardInterrupt:
    proc.terminate()
