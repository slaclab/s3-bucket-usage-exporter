#!/usr/bin/env python3

import os
import subprocess
import json
import time
from collections import deque
from prometheus_client import start_http_server, Summary, REGISTRY
from prometheus_client.core import GaugeMetricFamily, REGISTRY

from functools import wraps
from loguru import logger
import click

from typing import List

def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        logger.info(f"Function {func.__name__}{args} {kwargs} took {total_time:.4f} seconds")
        return result
    return timeit_wrapper

class S3Metrics:
    def __init__(self, bucket_alias: str, path: List[str], depth: int, sleep: int=300):
        self.bucket_alias = bucket_alias
        self.path = path
        self.path = [bucket_alias + p for p in self.path] # add bucket prefix
        self.depth = depth
        self.sleep = sleep
        self.reset_metrics()

    def reset_metrics(self):
        self.s3_usage_metric = GaugeMetricFamily(
                                    's3_bucket_usage',
                                    'Size of data on path in s3',
                                    labels=["bucket", "path", "units"]
                                )

    def run_metrics_loop(self):
        self.reset_metrics()
        while(True):
            self.fetch()
            time.sleep(self.sleep)

    def fetch(self):
        q = deque()
        for item in self.path:
            logger.info(f"Item: {item}")
            # get children
            retcode, results, stderr = mc_ls(item)
            if retcode == 0:
                for data in results:
                    nxt = data['key']
                    nxt_t = data['type'] # want folders only
                    logger.debug(f"got {item}{nxt}")
                    if nxt_t == "folder" and nxt != '/': # avoid '/' case
                        full_next = item + nxt
                        if full_next.count('/') - item.count('/') <= self.depth: 
                            q.append(full_next)
        scanned = dict()
        for item in q:
            # get size data
            if item not in scanned:
                retcode, results, stderr = mc_du(item)
                prefix = results[0]['prefix']
                size = results[0]['size']
                self.s3_usage_metric.add_metric([self.bucket_alias, prefix, "bytes"], size)
                scanned[item] = size
            
    def collect(self):
        yield self.s3_usage_metric

def exe( command: List[str] ):
    logger.info(f"running: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True)
    #logger.debug(f"parsed output: {result}")
    out = []
    for obj in result.stdout.strip().split("\n"):
        this = json.loads(obj)
        out.append( this )
    return result.returncode, out, result.stderr

def mc_ls(path):
    return exe( command=("mc", "ls", path, "--json") )

@timeit
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
  "--path",
  multiple=True,
  default=["/"],
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
def main( bucket_alias, path, depth, port, sleep ):
    s3_metrics = S3Metrics(bucket_alias=bucket_alias, path=path, depth=depth, sleep=sleep )
    REGISTRY.register( s3_metrics ) # triggers collect method
    logger.info(f"starting webserver on port {port} for {bucket_alias}: using depth {depth} with polling periodicity of {sleep}")
    start_http_server(port)
    s3_metrics.run_metrics_loop()

if __name__ == "__main__":
    main( auto_envvar_prefix="S3_BUCKET_USAGE")
