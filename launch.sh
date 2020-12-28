#!/bin/bash

docker run --restart always \
           -v "$PWD"/counts:/bot/counts \
           -v "$PWD"/group_db.txt:/bot/group_db.txt \
           -e TOKEN="voleeeevi" \
           -e CST_CID="ti piacerebbe" \
           -itd asdbot:latest