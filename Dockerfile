FROM python:3.9-slim-buster

# install XKCD font
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get install -y --no-install-recommends fonts-humor-sans \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /bot/counts
COPY requirements.txt /bot
WORKDIR /bot
# install requirements as soon as possible so rebuilds are faster
RUN pip3 install -r requirements.txt
COPY asd_bot_multigroup.py ./
COPY motivational_replies.py ./

ENV COUNTS_DIR="/bot/counts/"
ENV GROUP_DB="group_db.txt"
ENV DB_FILE="_past_asd.txt"
ENV CNT_FILE="_current_count.txt"
ENV GRAPH_FILE="_history_graph.png"

CMD ["python", "-u", "asd_bot_multigroup.py"]

# build with
#   docker build -t asdbot .
# run with
# -e TOKEN=... -e CST_CID=...
