from __future__ import annotations

import logging
from pathlib import Path
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for
from ldap3.utils.conv import escape_filter_chars

from .config import Config
from .ldap_client import LDAPClient
from .winrm_client import WinRMClient


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    audit_log_path = Path(app.config["AUDIT_LOG_PATH"])
    audit_log_path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        filename=audit_log_path,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    ldap_client = LDAPClient(app.config)
    winrm_client = WinRMClient(app.config)

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("user"):
                return redirect(url_for("login"))
            return view(*args, **kwargs)

        return wrapped

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            if not username or not password:
                flash("Username and password are required.", "error")
                return render_template("login.html")
            result = ldap_client.authenticate_user(
                app.config["LDAP_BASE_DN"],
                username,
                password,
                app.config["LDAP_ALLOWED_GROUP_DN"],
            )
            if result.error:
                flash(result.error, "error")
                return render_template("login.html")
            session["user"] = username
            flash("Login successful.", "success")
            return redirect(url_for("users"))
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.pop("user", None)
        flash("Logged out.", "success")
        return redirect(url_for("login"))

    @app.route("/users")
    @login_required
    def users():
        query = request.args.get("q", "").strip()
        ldap_filter = app.config["LDAP_USER_FILTER"]
        if query:
            escaped = escape_filter_chars(query)
            ldap_filter = f"(&{ldap_filter}(|(cn=*{escaped}*)(sAMAccountName=*{escaped}*)(mail=*{escaped}*)))"
        result = ldap_client.search(
            app.config["LDAP_BASE_DN"],
            ldap_filter,
            app.config["LDAP_USER_ATTRIBUTES"],
        )
        if result.error:
            flash(f"LDAP search error: {result.error}", "error")
        return render_template("users.html", users=result.entries, query=query)

    @app.route("/groups")
    @login_required
    def groups():
        query = request.args.get("q", "").strip()
        ldap_filter = app.config["LDAP_GROUP_FILTER"]
        if query:
            escaped = escape_filter_chars(query)
            ldap_filter = f"(&{ldap_filter}(|(cn=*{escaped}*)(description=*{escaped}*)))"
        result = ldap_client.search(
            app.config["LDAP_BASE_DN"],
            ldap_filter,
            app.config["LDAP_GROUP_ATTRIBUTES"],
        )
        if result.error:
            flash(f"LDAP search error: {result.error}", "error")
        return render_template("groups.html", groups=result.entries, query=query)

    @app.route("/users/<path:dn>/enable", methods=["POST"])
    @login_required
    def enable_user(dn: str):
        result = winrm_client.enable_account(dn)
        if result.error:
            flash(f"Enable failed: {result.error}", "error")
        else:
            _audit("enable_user", dn)
            flash("User enabled.", "success")
        return redirect(url_for("users"))

    @app.route("/users/<path:dn>/disable", methods=["POST"])
    @login_required
    def disable_user(dn: str):
        result = winrm_client.disable_account(dn)
        if result.error:
            flash(f"Disable failed: {result.error}", "error")
        else:
            _audit("disable_user", dn)
            flash("User disabled.", "success")
        return redirect(url_for("users"))

    @app.route("/users/<path:dn>/reset-password", methods=["POST"])
    @login_required
    def reset_password(dn: str):
        new_password = request.form.get("new_password", "").strip()
        if not new_password:
            flash("Password cannot be empty.", "error")
            return redirect(url_for("users"))
        result = winrm_client.reset_password(dn, new_password)
        if result.error:
            flash(f"Password reset failed: {result.error}", "error")
        else:
            _audit("reset_password", dn)
            flash("Password reset successful.", "success")
        return redirect(url_for("users"))

    def _audit(action: str, dn: str) -> None:
        actor = session.get("user", "unknown")
        logging.info("%s %s by %s", action, dn, actor)

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5000)
