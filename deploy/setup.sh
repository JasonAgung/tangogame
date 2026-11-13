#!/usr/bin/env bash
# Setup backend Tango di VPS Ubuntu (Oracle A1 / aarch64).
# Jalankan dari root repo sebagai user biasa (punya sudo):
#   ./deploy/setup.sh 168-110-212-220.sslip.io
# Aman dijalankan ulang (idempotent).
set -euo pipefail

DOMAIN="${1:?Pakai: ./deploy/setup.sh <domain>   contoh: 168-110-212-220.sslip.io}"
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
APP_USER="$(id -un)"

echo "==> App dir: $APP_DIR | user: $APP_USER | domain: $DOMAIN"

# 0. Pastikan port 80/443 tidak dipakai service lain selain Caddy
busy="$(sudo ss -ltnpH '( sport = :80 or sport = :443 )' | grep -v caddy || true)"
if [ -n "$busy" ]; then
  echo "!! Port 80/443 sudah dipakai proses lain:"; echo "$busy"
  echo "!! Hentikan dulu atau sesuaikan reverse proxy-nya secara manual."; exit 1
fi

# API Tango jalan di 127.0.0.1:8100, pastikan belum dipakai service lain
if sudo ss -ltnpH '( sport = :8100 )' | grep -v uvicorn | grep -q .; then
  echo "!! Port 8100 sudah dipakai proses lain. Ganti port di deploy/tango-api.service & deploy/tango.caddy."; exit 1
fi

# 1. Paket sistem
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip curl tzdata
if ! command -v caddy >/dev/null; then
  sudo apt-get install -y caddy || {
    echo "==> caddy tidak ada di repo Ubuntu, pakai repo resmi Caddy"
    sudo apt-get install -y debian-keyring debian-archive-keyring apt-transport-https gnupg
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor --yes -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list >/dev/null
    sudo apt-get update && sudo apt-get install -y caddy
  }
fi

# 2. Python venv + dependency
[ -d "$APP_DIR/venv" ] || python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install -q --upgrade pip
"$APP_DIR/venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"

# 3. Chromium untuk Playwright (dipakai scraper harian)
sudo "$APP_DIR/venv/bin/python" -m playwright install-deps chromium \
  || echo "!! playwright install-deps gagal (OS belum didukung resmi?). Lanjut, cek hasil scraper di bawah."
"$APP_DIR/venv/bin/python" -m playwright install chromium

# 4. Firewall di dalam VM (image Oracle default REJECT semua kecuali SSH)
command -v iptables >/dev/null || sudo apt-get install -y iptables
for port in 80 443; do
  if ! sudo iptables -C INPUT -p tcp --dport "$port" -m state --state NEW -j ACCEPT 2>/dev/null; then
    pos="$(sudo iptables -L INPUT --line-numbers -n | awk '$2=="REJECT"{print $1; exit}')"
    sudo iptables -I INPUT "${pos:-1}" -p tcp --dport "$port" -m state --state NEW -j ACCEPT
  fi
done
command -v netfilter-persistent >/dev/null && sudo netfilter-persistent save

# 5. systemd: API + timer scraper
for unit in tango-api.service tango-daily.service tango-daily.timer; do
  sed -e "s#__APP_DIR__#$APP_DIR#g" -e "s#__USER__#$APP_USER#g" "$APP_DIR/deploy/$unit" \
    | sudo tee "/etc/systemd/system/$unit" >/dev/null
done
sudo systemctl daemon-reload
sudo systemctl enable --now tango-api.service
sudo systemctl enable --now tango-daily.timer

echo "==> Tes scraper sekali..."
sudo systemctl start tango-daily.service || true
sudo journalctl -u tango-daily.service -n 5 --no-pager

# 6. Caddy (HTTPS otomatis). Config Caddy lain yang sudah ada tidak ditimpa.
sed "s#__DOMAIN__#$DOMAIN#g" "$APP_DIR/deploy/tango.caddy" | sudo tee /etc/caddy/tango.caddy >/dev/null
if grep -q "root \* /usr/share/caddy" /etc/caddy/Caddyfile 2>/dev/null; then
  echo "import /etc/caddy/tango.caddy" | sudo tee /etc/caddy/Caddyfile >/dev/null   # Caddyfile bawaan, ganti
elif ! grep -q "import /etc/caddy/tango.caddy" /etc/caddy/Caddyfile 2>/dev/null; then
  echo "import /etc/caddy/tango.caddy" | sudo tee -a /etc/caddy/Caddyfile >/dev/null
fi
sudo systemctl enable caddy
sudo systemctl reload caddy || sudo systemctl restart caddy

echo
echo "==> Selesai. Cek dari laptop:  curl https://$DOMAIN/api/daily"
echo "    (Pastikan Ingress Rule port 80 & 443 sudah dibuka di Security List VCN Oracle.)"
