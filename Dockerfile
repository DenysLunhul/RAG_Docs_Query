FROM ubuntu:latest
LABEL authors="denys"

ENTRYPOINT ["top", "-b"]