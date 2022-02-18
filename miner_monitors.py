import json
import requests
import socket
import util

class PhoenixMinerMonitor(object):
    def __init__(self, ip, port, **kwargs):
        self.address = (ip, port)
        self.message = b'{"id": 0, "jsonrpc": "2.0", "method": "miner_getstat1"}\r\n\r\n'
        if kwargs:
            print("unused arguments: {}".format(kwargs))

    def get_status(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect(self.address)
            s.sendall(self.message)
            data = s.recv(4096)
        try:
            results = json.loads(data.decode())
        except Exception:
            print("Exception happens when loading response to json...")
            print(data)
            return {}

        content = results["result"]
        hashrate, accepted_shares, rejected_shares = content[2].split(";")
        invalid_shares = int(content[8].split(";")[0])
        hashrate = float(hashrate) * 1000
        accepted_shares = int(accepted_shares)
        rejected_shares = int(rejected_shares)
        parsed = {
            "id": results['id'],
            "name": "AMD Radeon RX 5700",
            "uptime": util.minutes_to_interval(float(content[1])),
            "hashrate": hashrate,
            "accepted_shares": accepted_shares,
            "rejected_shares": rejected_shares,
            "invalid_shares": invalid_shares,
            "latency": 24,
        }
        return parsed

class NBMinerMonitor(object):
    def __init__(self, ip, port, **kwargs):
        self.endpoint = "http://{}:{}/api/v1/status".format(ip, port)
        if kwargs:
            print("unused arguments: {}".format(kwargs))

    def get_status(self):
        response = requests.get(self.endpoint, timeout=5)
        try:
            results = response.json()
        except Exception:
            print("Exception happens when loading response to json...")
            print(response.text)
            return {}
        results["uptime"] = util.timestamp_to_now(results["start_time"])
        return results

class GPUZMonitor(object):
    def __init__(self, ip, port, enable_list, **kwargs):
        self.enables = {field: str(i) for field, i in enable_list.items()}
        enable_str = ','.join(self.enables.values())
        self.endpoint = "http://{}:{}/json.json?enable={}".format(ip, port, enable_str)
        if kwargs:
            print("unused arguments: {}".format(kwargs))

    def get_status(self):
        response = requests.get(self.endpoint, timeout=5)
        try:
            results = response.json()
        except Exception:
            print("Exception happens when loading response to json...")
            print(response.text)
            return {}

        sensor = results["gpuz"]["sensors"]
        parsed = {field: sensor[i]["value"] for field, i in self.enables.items()}
        return parsed

class CPUMinerMonitor(object):
    def __init__(self, ip, port, **kwargs):
        self.address = (ip, port)
        self.message = b"summary"
        if kwargs:
            print("unused arguments: {}".format(kwargs))

    def get_status(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect(self.address)
            s.sendall(self.message)
            data = s.recv(4096)

        data = data.decode().split("|")[0]
        contents = data.split(";")
        name_mapping = {
            "HS": ("hashrate", float),
            "ACC": ("accepted_shares", int),
            #"ACCMN": ("accepted_shares_per_min", float)
            "REJ": ("rejected_shares", int),
            "SOL": ("invalid_shares", int),
            "UPTIME": ("uptime", float),
            #"TS": ("last_update", float),
        }
        parsed = {}
        for content in contents:
            key, value = content.strip().split("=")
            key = key.strip()
            if key in name_mapping:
                name, formatter = name_mapping[key]
                parsed[name] = formatter(value.strip())
        parsed["latency"] = 24
        return parsed

class XMRigMinerMonitor(object):
    def __init__(self, ip, port, **kwargs):
        self.endpoint = "http://{}:{}/2/summary".format(ip, port)
        if kwargs:
            print("unused arguments: {}".format(kwargs))

    def get_status(self):
        response = requests.get(self.endpoint, timeout=5)
        try:
            results = response.json()
        except Exception:
            print("Exception happens when loading response to json...")
            print(response.text)
            return {}

        try:
            invalid_shares = results["results"]["shares_total"] - results["results"]["shares_good"]
            results["results"]["shares_invalid"] = invalid_shares
        except Exception:
            pass
        return results

MINER_MONITORS = {
    "NBMinerMonitor": NBMinerMonitor,
    "PhoenixMinerMonitor": PhoenixMinerMonitor,
    "GPUZMonitor": GPUZMonitor,
    "CPUMinerMonitor": CPUMinerMonitor,
    "XMRigMinerMonitor": XMRigMinerMonitor,
}
