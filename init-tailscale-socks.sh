#!/bin/bash -x

sudo tailscale down 2>/dev/null
sudo chmod 644 /etc/default/tailscaled
sudo sed -i 's/^FLAGS=".*"$/FLAGS="--tun=userspace-networking --socks5-server=0.0.0.0:1055 --outbound-http-proxy-listen=0.0.0.0:1055"/' /etc/default/tailscaled
sudo tailscale up --accept-routes
sudo systemctl restart tailscaled.service
