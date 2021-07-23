FROM ubuntu:bionic
ENV DEBIAN_FRONTEND=noninteractive 

RUN apt-get update && apt-get install --no-install-recommends --yes \
  python3 \
  python3-pip \
	wget
WORKDIR /

# Download and install CaPTk tool, then remove its binary.
RUN wget --no-check-certificate \
  https://captk.projects.nitrc.org/CaPTk_1.8.1_Installer_centos7.bin
RUN chmod +x CaPTk_1.8.1_Installer_centos7.bin
RUN ./CaPTk_1.8.1_Installer_centos7.bin
RUN rm CaPTk_1.8.1_Installer_centos7.bin

# Download nibabel package for validation
RUN pip3 install nibabel

COPY validate.py /usr/local/bin/validate.py
COPY score.py /usr/local/bin/score.py
