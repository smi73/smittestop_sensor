FROM balenalib/raspberry-pi-debian-python:3.7-buster-run



# -- Start of wifi-connect section -- #
RUN install_packages dnsmasq wireless-tools
WORKDIR /usr/src/app
#RUN curl https://api.github.com/repos/balena-io/wifi-connect/releases/latest -s | grep -hoP 'browser_download_url": "\K.*%%BALENA_ARCH%%\.tar\.gz' | xargs -n1 curl -Ls | tar -xvz -C /usr/src/app/
#https://api.github.com/balena-io/wifi-connect/releases/download/v4.3.2/wifi-connect-v4.3.2-linux-rpi.tar.gz
#https://github.com/balena-io/wifi-connect/releases/download/v4.3.2/wifi-connect-v4.3.2-linux-rpi.tar.gz
RUN curl -s https://api.github.com/repos/balena-io/wifi-connect/releases/latest \
  | grep browser_download_url \
  | grep rpi \
  | cut -d '"' -f 4 \
  | xargs -n1 curl -Ls | tar -xvz -C /usr/src/app/
# -- End of wifi-connect section -- #
WORKDIR /usr/app
COPY pip.conf /etc/

RUN install_packages \
  cron \
  libatlas3-base \
  libgfortran3 \
  libzstd1 \
  liblcms2-2 \
  libjbig0 \
  libopenjp2-7 \
  libwebpdemux2 \
  libtiff5 \
  libwebpmux3 \
  libwebp6 \
  libxcb1 \
  libfreetype6-dev \
  bluetooth \
  python-dev \
  libbluetooth-dev \
  libcap2-bin

CMD ["/sbin/setcap","'cap_net_raw,cap_net_admin+eip' $(readlink -f $(which python))"]

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY start.sh .
COPY run-update.sh .
COPY lib lib
COPY fonts fonts
COPY bitmaps bitmaps

RUN chmod +x start.sh
RUN chmod +x run-update.sh

COPY smittestop.py .
CMD ["/bin/bash","start.sh"]