#!/bin/bash

mc alias set $bucket https://$bucket.sdf.slac.stanford.edu $access_key $secret_key

IFS=',' read -r -a paths_array <<< "$PATHS"

script_args="--bucket_alias $bucket"
for path in "${paths_array[@]}"; do
    script_args+=" --path $path"
done

script_args+=" --sleep $SLEEP_TIME"

./s3-bucket-usage-exporter.py $script_args

while true; do sleep 5s; done
