#!/usr/bin/env python3

import os
import subprocess
import json
from collections import deque
from prometheus_client import start_http_server, Summary, REGISTRY
from prometheus_client.core import GaugeMetricFamily, REGISTRY

from loguru import logger
import click

from typing import List

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

def generateTree( q: deque, depth: int ) -> str:
    root = q[0] # remember start point
    if depth == 0:
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

    Q = deque()
    Q.append( bucket_alias )
    logger.info(f"First Q: {Q}")
    for path in generateTree( Q, depth ):
       logger.warning(f"need to du {path}")

if __name__ == "__main__":
    main( )




