#!/bin/bash -x

sudo tailscale down 2>/dev/null
sudo chmod 644 /etc/default/tailscaled
sudo sed -i 's/^FLAGS=".*"$/FLAGS="--socks5-server=0.0.0.0:1055 --outbound-http-proxy-listen=0.0.0.0:1055"/' /etc/default/tailscaled
sudo systemctl restart tailscaled.service
sudo tailscale up --accept-routes --accept-dns=false
