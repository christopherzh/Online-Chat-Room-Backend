#!/bin/bash
#nohup uvicorn im_system:app --host 0.0.0.0 --port 8000 &
#uvicorn ws_system:app --host 0.0.0.0 --port 8001

## start 1
#uvicorn im_system:app --host 0.0.0.0 --port 8000  > /var/log/im_system.log 2>&1 &
## start 2
uvicorn ws_system:app --host 0.0.0.0 --port 8001 > /var/log/ws_system.log 2>&1 &
#
## just keep this script running
## shellcheck disable=SC2160
#while true ; do
#    sleep 1
#done