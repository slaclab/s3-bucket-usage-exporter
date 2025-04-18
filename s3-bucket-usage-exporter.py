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

SLEEP = int(os.environ.get("S3_COLLECTOR_INTERVAL", 60)) 
PORT = int(os.environ.get("S3_COLLECTOR_PORT", 8000))
MIN_SIZE = int(os.environ.get("S3_MIN_SIZE", 15000000000)) # 15gb

class S3Metrics:
    def __init__(self, bucket_alias: str, depth: int, sleep: int=300):
        self.bucket_alias = bucket_alias
        self.depth = depth
        self.sleep = sleep
        self.reset_metrics()

    def reset_metrics(self):
        self.s3_usage_metric = GaugeMetricFamily(
                                    's3_bucket_usage',
                                    'Size of data on path in s3',
                                    labels=["prefix", "size"]
                                )

    def run_metrics_loop(self):
        self.reset_metrics()
        while(True):
            self.fetch()
            time.sleep(self.sleep)

    def fetch(self):
        q = deque()
        q.append(self.bucket_alias)
        logger.info(f"first Q: {q}")

        while len(q) > 0:
            current = q[-1] 
            q.pop()
            
            # get size data
            retcode, results, stderr = mc_du(current)
            prefix = results[0]['prefix']
            size = results[0]['size']
            self.s3_usage_metric.add_metric([prefix], size)

            # if > 1 tb, queue up children
            if size > MIN_SIZE:
                retcode, results, stderr = mc_ls(current)
                if retcode == 0:
                    for data in results:
                        nxt = data['key']
                        nxt_t = data['type'] # want folders only
                        logger.debug(f"got {current}{nxt}")
                        if nxt_t == "folder" and nxt != '/': # avoid '/' case
                            logger.debug(f"queue up {current}{next}")
                            full_next = current + nxt
                            q.append(full_next)
                            # don't worry about depth for now

    def collect(self):
        yield self.s3_usage_metric

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
@click.option(
  "--port",
  default=8000,
  show_default=True,
  help="port number to expose metrics for prometheus scrapes"
)
@click.option(
  "--sleep",
  default=3600,
  show_default=True
  help="periodicity of collecting usage information"
)
def main( bucket_alias, depth, port, sleep ):

    s3_metrics = S3Metrics(bucket_alias=bucket_alias, depth=depth, sleep=sleep )
    REGISTRY.register( s3_metrics ) # triggers collect method
    logger.info(f"starting webserver on port {port} for {bucket_alias}: using depth {depth} with polling periodicity of {sleep}")
    start_http_server(port)
    s3_metrics.run_metrics_loop()

if __name__ == "__main__":
    main( auto_envvar_prefix="S3_BUCKET_USAGE")




