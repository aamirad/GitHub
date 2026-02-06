from __future__ import annotations

import ssl
from dataclasses import dataclass
from typing import Iterable

from ldap3 import ALL, Connection, MODIFY_REPLACE, Server, Tls
from ldap3.core.exceptions import LDAPException
from ldap3.utils.conv import escape_filter_chars


@dataclass
class LDAPResult:
    entries: list
    error: str | None = None


class LDAPClient:
    def __init__(self, config):
        self.config = config

    def _server(self) -> Server:
        tls = None
        if self.config.LDAP_VERIFY_CERT:
            tls = Tls(validate=ssl.CERT_REQUIRED)
        else:
            tls = Tls(validate=ssl.CERT_NONE)
        return Server(self.config.LDAP_SERVER, get_info=ALL, tls=tls)

    def connect(self) -> Connection:
        connection = Connection(
            self._server(),
            user=self.config.LDAP_BIND_DN,
            password=self.config.LDAP_BIND_PASSWORD,
            auto_bind=not self.config.LDAP_USE_STARTTLS,
        )
        if self.config.LDAP_USE_STARTTLS:
            connection.open()
            connection.start_tls()
            connection.bind()
        return connection

    def search(self, base_dn: str, ldap_filter: str, attributes: Iterable[str]) -> LDAPResult:
        try:
            with self.connect() as connection:
                connection.search(base_dn, ldap_filter, attributes=attributes)
                return LDAPResult(list(connection.entries))
        except LDAPException as exc:
            return LDAPResult([], error=str(exc))

    def authenticate_user(self, base_dn: str, username: str, password: str, allowed_group_dn: str) -> LDAPResult:
        try:
            with self.connect() as connection:
                escaped = escape_filter_chars(username)
                connection.search(
                    base_dn,
                    f\"(&(objectCategory=person)(objectClass=user)(sAMAccountName={escaped}))\",
                    attributes=[\"distinguishedName\", \"memberOf\", \"cn\"],
                )
                if not connection.entries:
                    return LDAPResult([], error=\"User not found.\")
                user_entry = connection.entries[0]
                user_dn = user_entry.entry_dn
                member_of = {dn.lower() for dn in user_entry.memberOf.values} if hasattr(user_entry, \"memberOf\") else set()
                if allowed_group_dn and allowed_group_dn.lower() not in member_of:
                    return LDAPResult([], error=\"User is not in the allowed security group.\")

            user_connection = Connection(
                self._server(),
                user=user_dn,
                password=password,
                auto_bind=not self.config.LDAP_USE_STARTTLS,
            )
            if self.config.LDAP_USE_STARTTLS:
                user_connection.open()
                user_connection.start_tls()
                user_connection.bind()
            if not user_connection.bound:
                return LDAPResult([], error=\"Invalid credentials.\")
            user_connection.unbind()
            return LDAPResult([user_entry])
        except LDAPException as exc:
            return LDAPResult([], error=str(exc))

    def modify(self, dn: str, changes: dict) -> LDAPResult:
        try:
            with self.connect() as connection:
                connection.modify(dn, changes)
                if connection.result["result"] != 0:
                    return LDAPResult([], error=connection.result["message"])
                return LDAPResult([])
        except LDAPException as exc:
            return LDAPResult([], error=str(exc))

    def set_password(self, dn: str, new_password: str) -> LDAPResult:
        try:
            with self.connect() as connection:
                connection.extend.microsoft.modify_password(dn, new_password)
                if connection.result["result"] != 0:
                    return LDAPResult([], error=connection.result["message"])
                return LDAPResult([])
        except LDAPException as exc:
            return LDAPResult([], error=str(exc))

    def enable_account(self, dn: str, user_account_control: int) -> LDAPResult:
        enabled_value = user_account_control & ~0x2
        return self.modify(dn, {"userAccountControl": [(MODIFY_REPLACE, [enabled_value])]})

    def disable_account(self, dn: str, user_account_control: int) -> LDAPResult:
        disabled_value = user_account_control | 0x2
        return self.modify(dn, {"userAccountControl": [(MODIFY_REPLACE, [disabled_value])]})
