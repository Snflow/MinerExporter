# flockpool: https://flockpool.com/api/v1/wallets/rtm/RTKF8aYzVGi9aUjbhaffan6hEwbQvDpmkY
# ethermine: https://api.ethermine.org/miner/ffCd69D9EEc40b6A858cAd0daf30Ebc1A9287a85/workers

import json
import requests
import util
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class EthermineMonitor(object):
    def __init__(self, address, workerRigMap={}, **kwargs):
        self.endpoint = "https://api.ethermine.org/miner/{}/workers".format(address)
        self.endpoint_balance = "https://api.ethermine.org/miner/{}/currentStats".format(address)
        self.balance_cache = None
        self.worker_rig_map = workerRigMap
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
        balance = self.get_balance()
        try:
            parsed = {}
            # data is an array of object for each worker
            for worker in results["data"]:
                rig_name = self.worker_rig_map.get(worker['worker'], worker['worker'])
                worker['balance'] = balance
                parsed[rig_name] = worker
            return parsed
        except Exception as e:
            print("Exception happens when read worker data: {}".format(e))
            return {}

    def get_balance(self):
        # get balance in every two calls since the number of API calls on ethermine web is limited
        if self.balance_cache is not None:
            balance = self.balance_cache
            self.balance_cache = None
            return balance

        response = requests.get(self.endpoint_balance, timeout=5)
        try:
            results = response.json()
        except Exception:
            print("Exception happens when loading response to json...")
            print(response.text)
            return 0.0
        try:
            balance = results["data"]["unpaid"] / 1e18
        except Exception as e:
            print("Exception happens when read balance data: {}".format(e))
            balance = 0.0
        self.balance_cache = balance
        return balance

class FlockpoolMonitor(object):
    def __init__(self, address, workerRigMap={}, **kwargs):
        self.endpoint = "https://flockpool.com/api/v1/wallets/rtm/{}".format(address)
        self.worker_rig_map = workerRigMap
        if kwargs:
            print("unused arguments: {}".format(kwargs))

    def get_status(self):
        response = requests.get(self.endpoint, timeout=5, verify=False)
        try:
            results = response.json()
        except Exception:
            print("Exception happens when loading response to json...")
            print(response.text)
            return {}
        balance = self.get_balance(results)
        try:
            parsed = {}
            # workers is an array of object for each worker
            for worker in results["workers"]:
                rig_name = self.worker_rig_map.get(worker['name'], worker['name'])
                worker['balance'] = balance
                parsed[rig_name] = worker
            return parsed
        except Exception as e:
            print("Exception happens when read worker data: {}".format(e))
            return {}

    def get_balance(self, results):
        try:
            balance = (results["balance"]["mature"] + results["balance"]["immature"]) / 1e8
        except Exception as e:
            print("Exception happens when read balance data: {}".format(e))
            balance = 0.0
        return balance

POOL_MONITORS = {
    "EthermineMonitor": EthermineMonitor,
    "FlockpoolMonitor": FlockpoolMonitor,
}
