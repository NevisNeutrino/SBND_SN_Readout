import sys
import time
import os
import platform
import subprocess
import socket
import glob

monitor_volumes = [
    '/data',
    # '/', 
    # '/daq/software',
    # '/daq/scratch',
    # '/daq/log',
    # '/daq/run_records',
    # '/home/nfs'
]

this_hostname = socket.gethostname().split('.', 1)[0]
this_experiment = 'sbnd'

grafana_host = ''   # fill in your Grafana host
grafana_port = 0    # fill in your Grafana port
grafana_timeout = 0.1

# CONFIG: threshold above which to delete files
delete_threshold_upper = 0.205   # 90% usage
delete_threshold_lower = 0.204
# CONFIG: directories to clean up if threshold exceeded
cleanup_dirs = ['/data']

def get_volume_metrics(volumes):
    now = int(time.time())
    results = []
    for v in volumes:
        name = v.replace('/','',1).replace('/','_')
        if len(name) == 0:
            name = 'root'

        st = os.statvfs(v)
        free_space_gb = round(st.f_bavail * st.f_frsize / 1024 / 1024 / 1024, 2)
        percent_used = 1.0 - (st.f_bavail / st.f_blocks)
        
        results.append("%s.%s.%s.Free_Space_GB %s %d" % (this_experiment, this_hostname, name, free_space_gb, now))
        results.append("%s.%s.%s.Percent_Used %s %d"  % (this_experiment, this_hostname, name, round(percent_used, 4), now))

        print(f"[INFO] Volume: {v}, Used: {percent_used*100:.1f}%, Free: {free_space_gb:.2f} GB")

        if percent_used >= delete_threshold_upper:
            print(f"[WARNING] Disk usage {percent_used*100:.1f}% exceeds threshold {delete_threshold_upper*100:.0f}% on {v}")
            cleanup_old_files(v)

    return '\n'.join(results) + '\n'

def cleanup_old_files(volume):
    # Only delete in configured directories that match this volume
    for d in cleanup_dirs:
        if not d.startswith(volume):
            continue

        print(f"[ACTION] Cleaning up files in {d}")
        # Get list of files ordered by modification time (oldest first)
        files = sorted(glob.glob(os.path.join(d, '*')), key=lambda f: os.path.getmtime(f))

        for f in files:
            if os.path.isfile(f):
                try:
                    os.remove(f)
                    print(f"[DELETE] Removed file: {f}")

                    # Re-check disk usage
                    st = os.statvfs(volume)
                    percent_used = 1.0 - (st.f_bavail / st.f_blocks)
                    if percent_used < delete_threshold_lower:
                        print(f"[INFO] Disk usage dropped below threshold: {percent_used*100:.1f}%")
                        return
                except Exception as e:
                    print(f"[ERROR] Failed to delete {f}: {e}")
            # optional: handle directories, but be careful with recursive deletion!

# sock = socket.socket()
# try:
#     sock.connect((grafana_host, grafana_port))
#     sock.settimeout(grafana_timeout)
# except:
#     print("Couldn't connect to Grafana server")
#     sys.exit(1)

metrics = get_volume_metrics(monitor_volumes)
# sock.sendall(bytearray(metrics, 'utf-8'))

print(metrics)