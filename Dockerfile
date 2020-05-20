FROM debian:buster

RUN apt-get update && apt-get install -y live-build
RUN sed -i '1161s%umount%#umount%' /usr/share/debootstrap/functions
CMD ["bash"]
