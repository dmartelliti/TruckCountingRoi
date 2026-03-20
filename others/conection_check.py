import subprocess

ips = ()

for i in range(1, 255):
    ip = f"{base}.{i}"
    result = subprocess.run(
        ["ping", "-n", "1", "-w", "200", ip],
        stdout=subprocess.DEVNULL
    )
    if result.returncode == 0:
        print("OK ->", ip)
