import os


def _get_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    SECRET_KEY = os.environ.get("ADUC_SECRET_KEY", "change-me")

    LDAP_SERVER = os.environ.get("ADUC_LDAP_SERVER", "ldaps://ad.example.com")
    LDAP_BASE_DN = os.environ.get("ADUC_LDAP_BASE_DN", "DC=example,DC=com")
    LDAP_BIND_DN = os.environ.get("ADUC_LDAP_BIND_DN", "CN=svc-aduc,OU=Service Accounts,DC=example,DC=com")
    LDAP_BIND_PASSWORD = os.environ.get("ADUC_LDAP_BIND_PASSWORD", "")
    LDAP_USE_STARTTLS = _get_bool(os.environ.get("ADUC_LDAP_USE_STARTTLS"))
    LDAP_VERIFY_CERT = _get_bool(os.environ.get("ADUC_LDAP_VERIFY_CERT"), True)

    LDAP_USER_FILTER = os.environ.get(
        "ADUC_LDAP_USER_FILTER",
        "(&(objectCategory=person)(objectClass=user))",
    )
    LDAP_GROUP_FILTER = os.environ.get(
        "ADUC_LDAP_GROUP_FILTER",
        "(objectClass=group)",
    )
    LDAP_USER_ATTRIBUTES = os.environ.get(
        "ADUC_LDAP_USER_ATTRIBUTES",
        "cn,sAMAccountName,displayName,mail,userAccountControl,memberOf,distinguishedName",
    ).split(",")
    LDAP_GROUP_ATTRIBUTES = os.environ.get(
        "ADUC_LDAP_GROUP_ATTRIBUTES",
        "cn,description,distinguishedName,member",
    ).split(",")

    LDAP_ALLOWED_GROUP_DN = os.environ.get("ADUC_LDAP_ALLOWED_GROUP_DN", "")

    WINRM_HOST = os.environ.get("ADUC_WINRM_HOST", "10.0.0.10")
    WINRM_USER = os.environ.get("ADUC_WINRM_USER", "DOMAIN\\\\aduc-operator")
    WINRM_PASSWORD = os.environ.get("ADUC_WINRM_PASSWORD", "")
    WINRM_TRANSPORT = os.environ.get("ADUC_WINRM_TRANSPORT", "ntlm")
    WINRM_USE_SSL = _get_bool(os.environ.get("ADUC_WINRM_USE_SSL"))
    WINRM_PORT = int(os.environ.get("ADUC_WINRM_PORT", "5985"))

    AUDIT_LOG_PATH = os.environ.get("ADUC_AUDIT_LOG_PATH", "/var/log/aduc-web/audit.log")
