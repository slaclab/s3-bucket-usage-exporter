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
        r = test_path()
        prefix = r[0]['prefix'] 
        size = r[0]['size']
        self.s3_usage_metric.add_metric(prefix, size)

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


def test_path():
    path = "rubin-embs3/rubin-summit-users/LSSTComCam/runs/DRP/DP1-RC1/w_2025_02/DM-48371/hips/deep/"
    retcode, results, stderr = mc_du(path)
    return results

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
  show_default=True,
  help="periodicity of collecting usage information"
)
def main( bucket_alias, depth, port, sleep ):

    s3_metrics = S3Metrics( bucket_alias=bucket_alias, depth=depth, sleep=sleep )
    REGISTRY.register( s3_metrics )
    logger.info(f"starting webserver on port {port} for {bucket_alias}: using depth {depth} with polling periodicity of {sleep}")
    start_http_server(port)
    s3_metrics.run_metrics_loop()

if __name__ == "__main__":
    main( auto_envvar_prefix="S3_BUCKET_USAGE" )




