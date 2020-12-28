#!/bin/bash

WD=/bot
CNT=counts
GDB=group_db.txt

docker run --restart unless-stopped \
           -v "$PWD"/$CNT:$WD/$CNT \
           -v "$PWD"/$GDB:$WD/$GDB \
           -e TOKEN="voleeeevi" \
           -e CST_CID="ti piacerebbe" \
           -itd asdbot:latest