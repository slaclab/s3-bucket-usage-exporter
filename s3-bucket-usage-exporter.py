#!/usr/bin/env python3

import os
import subprocess
import json
import time
from collections import deque
from prometheus_client import start_http_server, Summary, REGISTRY
from prometheus_client.core import GaugeMetricFamily, REGISTRY

from loguru import logger
import click

from typing import List


SLEEP = int(os.environ.get("S3_COLLECTOR_INTERVAL", 86400)) 
PORT = int(os.environ.get("S3_COLLECTOR_PORT", 8000))

class S3Metrics:
    def __init__(self, bucket_alias, depth):
        self.bucket_alias = bucket_alias
        self.depth = depth
        print(self.bucket_alias)
        print(self.depth)
        self.s3_usage_metric = GaugeMetricFamily(
                                    's3_bucket_usage',
                                    'Size of data on path in s3',
                                    labels=["prefix", "size"]
                                )
        print(type(self.s3_usage_metric))

    def collect(self):
        paths = list()
        for path in generateTree( self.bucket_alias, self.depth ):
            logger.warning(f"need to du {path}")
            paths.append(path) 
        for path in paths:
            yield self.s3_usage_metric.add_metric([path, aggregateUsage(path)])

def exe( command: List[str] ):
    logger.info(f"running: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True)
    logger.debug(f"parsed output: {result}")
    out = []
    for obj in result.stdout.strip().split("\n"):
        this = json.loads(obj)
        out.append( this )
    return result.returncode, out, result.stderr

def mc_ls(path):
    return exe( command=("mc", "ls", path, "--json") )

def mc_du(path):
    return exe( command=("mc", "du", path, "--json") )

def generateTree( root : str, depth: int ) -> str:
    q = deque()
    q.append( root )
    logger.info(f"First Q: {q}")

    if depth == 0:
        yield q[0]
        return
    while len(q) > 0:
        current = q[0]
        q.popleft()
        
        # run mc ls on current path and separate objects into list
        retcode, results, stderr = mc_ls(current)
        if retcode == 0:
            # queue up new paths
            for data in results:
                nxt = data['key']
                nxt_t = data['type'] # want folders only
                logger.debug(f"got {current}{nxt}")
                if nxt_t == "folder" and nxt != '/': # avoid files and '/' case
                    full_next = current + nxt
                    if full_next.count('/') - root.count('/') == depth:
                        yield f"{current}{nxt}"
                    if full_next.count('/') - root.count('/') < depth: # limit
                        q.append(current + nxt)

def aggregateUsage(path):
    retcode, results, stderr = mc_du(path)
    return results[0]['size'] # one element list
        
@click.command()
@click.option(
  "--bucket_alias",
  default="rubin-embs3/",
  show_default=True,
  help="mc bucket alias name"
)
@click.option(
  "--depth",
  default=1,
  show_default=True,
  help="scanning depth of directory"
)
def main( bucket_alias, depth ):

    print(bucket_alias)
    print(depth)
    s3_metrics = S3Metrics(bucket_alias, depth)
    print("before registry")
    REGISTRY.register( s3_metrics )
    print("after registry")
    start_http_server(PORT)
        
    while True:
        time.sleep(SLEEP)

if __name__ == "__main__":
    main()




