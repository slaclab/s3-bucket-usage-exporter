#!/bin/bash

mc alias set rubin-embs3 https://sdfembs3.sdf.slac.stanford.edu $access_key $secret_key

#mc du rubin-embs3/rubin-summit-users/LSSTComCam/calib/DM-46360 --json

./embargo-monitor.py

while true; do sleep 5s; done
