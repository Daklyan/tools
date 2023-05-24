#!/bin/sh

docker run --cap-add=NET_ADMIN -d \
	--name=transmission \
	--restart=always \
	-v /mnt/hdd_8to/tmp_dl:/mnt/hdd_8to/tmp_dl \
	-v /etc/localtime:/etc/locatime:ro \
	-e CREATE_TUN_DEVICE=true \
	-e OPENVPN_PROVIDER=PROTONVPN \
	-e OPENVPN_CONFIG=uk.protonvpn.net.udp \
	-e OPENVPN_USERNAME=TO_CHANGE \
	-e OPENVPN_PASSWORD=TO_CHANGE \
	-e WEBPROXY_ENABLED=false \
	-e LOCAL_NETWORK=192.168.1.0/24 \
	-e TRANSMISSION_DOWNLOAD_DIR=/mnt/hdd_8to/tmp_dl \
	--log-driver json-file \
	--log-opt max-size=10m \
	-p 9091:9091 \
	--cpuset-cpus="0-1" \
	--memory="2g" \
	haugene/transmission-openvpn

