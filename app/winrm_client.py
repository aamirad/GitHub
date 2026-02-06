from __future__ import annotations

from dataclasses import dataclass

import winrm


@dataclass
class WinRMResult:
    error: str | None = None


class WinRMClient:
    def __init__(self, config):
        self.config = config

    def _session(self) -> winrm.Session:
        return winrm.Session(
            target=f"{self.config.WINRM_HOST}:{self.config.WINRM_PORT}",
            auth=(self.config.WINRM_USER, self.config.WINRM_PASSWORD),
            transport=self.config.WINRM_TRANSPORT,
            server_cert_validation="validate" if self.config.WINRM_USE_SSL else "ignore",
        )

    @staticmethod
    def _escape_ps(value: str) -> str:
        return value.replace("'", "''")

    def run_ps(self, script: str) -> WinRMResult:
        response = self._session().run_ps(script)
        if response.status_code != 0:
            error = response.std_err.decode(errors="ignore") or "PowerShell error"
            return WinRMResult(error=error)
        return WinRMResult()

    def enable_account(self, dn: str) -> WinRMResult:
        safe_dn = self._escape_ps(dn)
        script = f"Import-Module ActiveDirectory; Enable-ADAccount -Identity '{safe_dn}'"
        return self.run_ps(script)

    def disable_account(self, dn: str) -> WinRMResult:
        safe_dn = self._escape_ps(dn)
        script = f"Import-Module ActiveDirectory; Disable-ADAccount -Identity '{safe_dn}'"
        return self.run_ps(script)

    def reset_password(self, dn: str, new_password: str) -> WinRMResult:
        safe_dn = self._escape_ps(dn)
        safe_pw = self._escape_ps(new_password)
        script = (
            "Import-Module ActiveDirectory; "
            f"$secure = ConvertTo-SecureString '{safe_pw}' -AsPlainText -Force; "
            f"Set-ADAccountPassword -Identity '{safe_dn}' -NewPassword $secure -Reset"
        )
        return self.run_ps(script)
