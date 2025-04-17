#!/usr/bin/env python3

import os
import subprocess
import json
from collections import deque
from prometheus_client import start_http_server, Summary, REGISTRY
from prometheus_client.core import GaugeMetricFamily, REGISTRY

def mc_ls(path):
    command = ["mc", "ls", path, "--json"]
    result = subprocess.run(command, capture_output=True, text=True)
    return result

def generateTree():
    if len(q) == 0:
        return
    current = q[0]
    q.popleft()
    
    # run mc ls on current path and separate objects into list
    result = mc_ls(current)
    if result.stdout != '':
        json_objects = result.stdout.strip().split('\n')

        # queue up new paths
        for obj in json_objects:
            data = json.loads(obj)
            nxt = data['key']
            if nxt[-1] == '/':
                full_next = current + nxt
                if full_next.count('/') <= 5: # depth limit
                    paths.append(current + nxt)
                    q.append(current + nxt)
    generateTree()

   

root = "rubin-embs3/"
paths = list()
paths.append(root)
q = deque()
q.append(root)

def main():
    generateTree()

if __name__ == "__main__":
    main()




