# ADUC Web Console

Production-ready web console for managing Active Directory users and groups via LDAP.

## Features

- LDAP/Active Directory search for users and groups
- Enable/disable user accounts via WinRM PowerShell
- Reset passwords via WinRM PowerShell
- Audit logging to `/var/log/aduc-web/audit.log`
- Gunicorn + systemd + Nginx deployment

## Quick start (Ubuntu)

```bash
sudo ./aduc.manage.sh
```

Then edit the environment file and restart the service:

```bash
sudo nano /etc/aduc-web/aduc-web.env
sudo systemctl restart aduc-web
```

## Environment configuration

Copy `.env.example` to `/etc/aduc-web/aduc-web.env` and update the values.

| Variable | Description |
| --- | --- |
| `ADUC_SECRET_KEY` | Flask secret key |
| `ADUC_LDAP_SERVER` | LDAP URI (ldaps:// or ldap://) |
| `ADUC_LDAP_BASE_DN` | Base DN for searches |
| `ADUC_LDAP_BIND_DN` | Bind DN for service account |
| `ADUC_LDAP_BIND_PASSWORD` | Bind password |
| `ADUC_LDAP_USE_STARTTLS` | Enable StartTLS on ldap:// |
| `ADUC_LDAP_VERIFY_CERT` | Validate LDAP certificate |
| `ADUC_LDAP_USER_FILTER` | LDAP filter for users |
| `ADUC_LDAP_GROUP_FILTER` | LDAP filter for groups |
| `ADUC_LDAP_USER_ATTRIBUTES` | LDAP attributes for users |
| `ADUC_LDAP_GROUP_ATTRIBUTES` | LDAP attributes for groups |
| `ADUC_LDAP_ALLOWED_GROUP_DN` | Security group allowed to access the web UI |
| `ADUC_WINRM_HOST` | Domain Controller host/IP for WinRM |
| `ADUC_WINRM_USER` | Domain account for WinRM operations |
| `ADUC_WINRM_PASSWORD` | Password for WinRM account |
| `ADUC_WINRM_TRANSPORT` | WinRM transport (ntlm) |
| `ADUC_WINRM_USE_SSL` | Enable WinRM over HTTPS |
| `ADUC_WINRM_PORT` | WinRM port |
| `ADUC_AUDIT_LOG_PATH` | Audit log path |

## Hardening recommendations

- Use LDAPS with a trusted certificate.
- Restrict the service account to the minimum required permissions.
- Use a dedicated AD security group for web console access.
- Ensure the WinRM account has only the required ADUC privileges.
- Enable WinRM on the Domain Controller (`Enable-PSRemoting`) and allow the AD module.
- Front with HTTPS (Nginx + certbot).
- Restrict network access to the web console.
