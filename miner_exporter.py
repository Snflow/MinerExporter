#!/usr/bin/python3

import sys
import json
import time
import math
import util
from miner_monitors import MINER_MONITORS
from pool_monitors import POOL_MONITORS
from hiveos_monitor import HiveOSMonitor
from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily, REGISTRY
from itertools import chain

MINER_MONITORS["HiveOSMonitor"] = HiveOSMonitor

class MinerJsonCollector(object):
    def __init__(self, config):
        self.monitors = {}
        for name, args in config["monitorArgs"].items():
            monitor = MINER_MONITORS[name](**args)
            self.monitors[name] = monitor
        self.metrics = {}
        for name, path in config["metrics"].items():
            self.metrics[name] = util.get_path(path)
        self.tag = {}
        for name, path in config["tag"].items():
            self.tag[name] = util.get_path(path)
        self.defaultLabels = config["defaultLabels"]

    def collect(self):
        results = {}
        for name, monitor in self.monitors.items():
            try:
                results[name] = monitor.get_status()
            except Exception as e:
                print("Exception happens when getting status from {}: {}".format(name, e))
                results[name] = {}

        metrics = {}
        for name, path in self.metrics.items():
            metrics[name] = util.get_value(results, path)
        tags = {}
        for name, path in self.tag.items():
            tags[name] = util.get_value(results, path)
            if not tags[name] or (isinstance(tags[name], float) and math.isnan(tags[name])):
                tags[name] = self.defaultLabels[name]
        return metrics, tags

class PoolJsonCollector(object):
    def __init__(self, config):
        self.monitors = {}
        for name, args in config["monitorArgs"].items():
            monitor = POOL_MONITORS[name](**args)
            self.monitors[name] = monitor
        self.metrics = {}
        for name, path in config["metrics"].items():
            self.metrics[name] = util.get_path(path)

    def collect(self):
        results = {}
        for monitor_name, monitor in self.monitors.items():
            try:
                status = monitor.get_status()
                for rig_name, result in status.items():
                    if rig_name not in results:
                        results[rig_name] = {}
                    results[rig_name][monitor_name] = result
            except Exception as e:
                print("Exception happens when getting status from {}: {}".format(monitor_name, e))
                pass

        metrics = {}
        for rig_name, result in results.items():
            if rig_name not in metrics:
                metrics[rig_name] = {}
            for name, path in self.metrics.items():
                metrics[rig_name][name] = util.get_value(result, path)
        return metrics


class MinerExporter(object):
    def __init__(self, config_file="./config.json"):
        with open(config_file) as f:
            config = json.load(f)
        self.miner_collectors = []
        for c in config["minerMonitors"]:
            self.miner_collectors.append(MinerJsonCollector(c))
        self.pool_collector = PoolJsonCollector(config["poolMonitors"])

    def collect_miner(self):
        for collector in self.miner_collectors:
            metrics, tags = collector.collect()

            label_names = []
            label_values = []
            for name in sorted(tags.keys()):
                label_names.append(name)
                label_values.append(str(tags[name]))

            for key, value in metrics.items():
                metric = GaugeMetricFamily(key, '', labels=label_names)
                metric.add_metric(label_values, value)
                yield metric

    def collect_pool(self):
        metrics = self.pool_collector.collect()
        label_names = ['id', 'name']
        for name, results in metrics.items():
            label_values = ['0', name]
            for key, value in results.items():
                metric = GaugeMetricFamily(key, '', labels=label_names)
                metric.add_metric(label_values, value)
                yield metric

    def collect(self):
        return chain(self.collect_miner(), self.collect_pool())

if __name__ == "__main__":
    if len(sys.argv) > 1:
        conf = sys.argv[1]
    else:
        conf = "./config.json"
    port = 9118
    print("loading configuration from {}".format(conf))
    REGISTRY.register(MinerExporter(conf))
    start_http_server(port)
    print("exporter listening on port {}".format(port))
    while True:
        time.sleep(1)
