import time
import requests
import util

class HiveOSMonitor(object):
    def __init__(self, farm_id, worker_id, **kwargs):
        base_url = 'https://api2.hiveos.farm/api/v2'
        self.stats_endpoint = "{}/farms/{}/workers/{}".format(base_url, farm_id, worker_id)
        self.refresh_endpoint = "{}/auth/refresh".format(base_url)

        self.token_file = "/home/snflow/MiningMonitor/hiveos/hiveosToken.txt"
        with open(self.token_file) as f:
            access_token = f.readline().strip()
            expiration = float(f.readline())
        if time.time() > expiration:
            raise RuntimeError("access token has expired")
        else:
            print("access token valid")

        self.header = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(access_token)
        }
        self.refresh_token()

        if kwargs:
            print("unused arguments: {}".format(kwargs))

    def refresh_token(self):
        now = time.time()
        response = requests.post(self.refresh_endpoint, headers=self.header)
        try:
            results = response.json()
        except Exception:
            print("Exception happens when loading response to json...")
            print(response.text)
            raise

        access_token = results["access_token"]
        self.header = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(access_token)
        }

        expires = results["expires_in"]
        with open(self.token_file, "w") as f:
            f.write(access_token)
            f.write("\n")
            f.write(str(now + expires))
            f.write("\n")
        print("token will expires in: {}s".format(results["expires_in"]))

    def get_status(self):
        response = requests.get(self.stats_endpoint, headers=self.header, timeout=5)
        try:
            results = response.json()
        except Exception:
            print("Exception happens when loading response to json...")
            print(response.text)
            return {}
        results['auxiliary'] = {
            "uptime": util.timestamp_to_now(results["stats"]["miner_start_time"]),
            "latency": 24,
            "eth_hashrate": results["miners_summary"]["hashrates"][0]["hash"] * 1000.0,
            "rtm_hashrate": results["miners_summary"]["hashrates"][1]["hash"] * 1000.0,
            "gpu_mem_temp": results["gpu_stats"][0]["temp"] + 20.0,
            "gpu_hot_temp": results["gpu_stats"][0]["temp"] + 9.0,
            "gpu_core_clock": 1095,
            "gpu_mem_clock": 9501
        }
        return results
