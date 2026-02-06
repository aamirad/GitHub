#!/usr/bin/env bash
set -euo pipefail

APP_USER="aduc"
APP_GROUP="aduc"
APP_DIR="/opt/aduc-web"
ENV_DIR="/etc/aduc-web"
ENV_FILE="$ENV_DIR/aduc-web.env"
SERVICE_FILE="/etc/systemd/system/aduc-web.service"
NGINX_SITE="/etc/nginx/sites-available/aduc-web"
NGINX_ENABLED="/etc/nginx/sites-enabled/aduc-web"

if [[ $EUID -ne 0 ]]; then
  echo "Please run as root." >&2
  exit 1
fi

apt-get update
apt-get install -y python3-venv python3-pip nginx rsync

if ! id "$APP_USER" >/dev/null 2>&1; then
  useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin "$APP_USER"
fi

mkdir -p "$APP_DIR" "$ENV_DIR" /var/log/aduc-web

rsync -a --delete --exclude '.git' --exclude 'venv' ./ "$APP_DIR"

python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --upgrade pip
"$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Starting interactive configuration..."
  read -rp "Active Directory (LDAP) server (e.g. ldaps://10.0.0.10): " LDAP_SERVER
  read -rp "LDAP Base DN (e.g. DC=example,DC=com): " LDAP_BASE_DN
  read -rp "LDAP Bind DN (service account): " LDAP_BIND_DN
  read -srp "LDAP Bind Password: " LDAP_BIND_PASSWORD
  echo
  read -rp "Allowed Admin Group DN (security group): " LDAP_ALLOWED_GROUP_DN
  read -rp "WinRM host/IP (Domain Controller): " WINRM_HOST
  read -rp "WinRM username (DOMAIN\\user): " WINRM_USER
  read -srp "WinRM password: " WINRM_PASSWORD
  echo
  read -rp "Web access IP (server IP for nginx server_name): " WEB_IP
  read -rp "Use StartTLS for LDAP? (true/false) [false]: " LDAP_USE_STARTTLS
  read -rp "Verify LDAP cert? (true/false) [true]: " LDAP_VERIFY_CERT

  LDAP_USE_STARTTLS=${LDAP_USE_STARTTLS:-false}
  LDAP_VERIFY_CERT=${LDAP_VERIFY_CERT:-true}

  cat > "$ENV_FILE" <<ENV
ADUC_SECRET_KEY=$(openssl rand -hex 32)
ADUC_LDAP_SERVER=${LDAP_SERVER}
ADUC_LDAP_BASE_DN=${LDAP_BASE_DN}
ADUC_LDAP_BIND_DN=${LDAP_BIND_DN}
ADUC_LDAP_BIND_PASSWORD=${LDAP_BIND_PASSWORD}
ADUC_LDAP_USE_STARTTLS=${LDAP_USE_STARTTLS}
ADUC_LDAP_VERIFY_CERT=${LDAP_VERIFY_CERT}
ADUC_LDAP_ALLOWED_GROUP_DN=${LDAP_ALLOWED_GROUP_DN}
ADUC_WINRM_HOST=${WINRM_HOST}
ADUC_WINRM_USER=${WINRM_USER}
ADUC_WINRM_PASSWORD=${WINRM_PASSWORD}
ADUC_WINRM_TRANSPORT=ntlm
ADUC_WINRM_USE_SSL=false
ADUC_WINRM_PORT=5985
ADUC_AUDIT_LOG_PATH=/var/log/aduc-web/audit.log
ENV
  chmod 600 "$ENV_FILE"
else
  read -rp "Web access IP (server IP for nginx server_name): " WEB_IP
fi

chown -R "$APP_USER":"$APP_GROUP" "$APP_DIR" "$ENV_DIR" /var/log/aduc-web

cp "$APP_DIR/deploy/aduc-web.service" "$SERVICE_FILE"

WEB_IP=${WEB_IP:-_}
cp "$APP_DIR/deploy/nginx.conf" "$NGINX_SITE"
sed -i "s/SERVER_NAME_PLACEHOLDER/${WEB_IP}/g" "$NGINX_SITE"

ln -sf "$NGINX_SITE" "$NGINX_ENABLED"
rm -f /etc/nginx/sites-enabled/default

systemctl daemon-reload
systemctl enable --now aduc-web
systemctl restart nginx

echo "Installation complete. Web UI available at http://${WEB_IP}/"
