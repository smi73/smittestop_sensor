FROM balenalib/raspberry-pi-debian-python:3.7-buster-run

# -- Start of wifi-connect section -- #
RUN install_packages dnsmasq wireless-tools wget
WORKDIR /usr/src/app
RUN curl -s https://api.github.com/repos/balena-io/wifi-connect/releases/latest \
  | grep browser_download_url \
  | grep rpi \
  | cut -d '"' -f 4 \
  | xargs -n1 curl -Ls | tar -xvz -C /usr/src/app/

COPY . .
# -- End of wifi-connect section -- #

WORKDIR /usr/app
COPY pip.conf /etc/

RUN install_packages \
  bluetooth \
  python-dev \
  libbluetooth-dev \
  libcap2-bin

CMD ["/sbin/setcap","'cap_net_raw,cap_net_admin+eip' $(readlink -f $(which python))"]


COPY requirements.txt .
RUN pip install -r requirements.txt

COPY start.sh .
COPY lib lib
COPY fonts fonts
COPY bitmaps bitmaps
COPY templates templates
COPY static static

RUN chmod +x start.sh

COPY smittestop.py .
CMD ["/bin/bash","start.sh"]