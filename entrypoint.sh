#!/bin/bash

mc alias set $bucket https://$bucket.sdf.slac.stanford.edu $access_key $secret_key

IFS=',' read -r -a paths_array <<< "$PATHS"
IFS=',' read -r -a depths_array <<< "$DEPTHS"

script_args="--bucket_alias $bucket"
for (( i=0; i<${#paths_array[@]}; i++ )); do
    path=${paths_array[i]}
    depth=${depths_array[i]}
    script_args+=" --path $path --depth $depth"
done

./s3-bucket-usage-exporter.py $script_args

while true; do sleep 5s; done
