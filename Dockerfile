FROM debian:stretch

RUN apt-get update && apt-get install -y live-build

CMD ["bash"]
