FROM python:3.9-alpine3.12
COPY asd_bot_multigroup.py /bot
COPY motivational_replies.py /bot
VOLUME "$PWD"/logs /bot/logs
VOLUME "$PWD"/counts /bot/counts
VOLUME "$PWD"/group_db.txt /bot/group_db.txt
ENV COUNTS_DIR="counts/"
ENV GROUP_DB="group_db.txt"
ENV DB_FILE="_past_asd.txt"
ENV CNT_FILE="_current_count.txt"
ENV GRAPH_FILE="_history_graph.png"
RUN pip install -r requirements.txt
WORKDIR /bot
CMD ["python", "-u", "asd_bot_multigroup.py", ">", "logs/log_$(date +%s).txt", "2>&1"]

# run with
# -e TOKEN=... -e CST_CID=...