from flask import request, render_template, url_for, redirect, make_response, session
from os import getenv
from datetime import datetime, timedelta


def setup(self):
    @self.route("/login-error", methods=["GET"])
    def login_error():
        respone = make_response(render_template("login-error.html" , locals=self.locals, url_for=url_for))
        respone.delete_cookie("token")
        return respone

    @self.route("/login/status", methods=["GET"])
    def login_callback_status():
        token = request.cookies.get("token")
        if not token:
            return {"status": "fail"}, 401
        if token not in self.discord.new_users:
            return {"status": "fail"}, 401
        status = self.discord.new_users[token][0]
        if status == "success":
            return {"status": "success"}, 200
        elif status == "wait":
            return {"status": "wait"}, 401
        else:
            return {"status": "fail"}, 401

    @self.route("/login-callback", methods=["GET"])
    def login_callback():
        if request.args.get("error"):
            return redirect(url_for("login_error"))
        code = request.args.get("code")
        connect_code = session.get("helix_code")
        if not connect_code:
            return redirect(url_for("login_error"))
        self.discord.new_users[connect_code] = ["wait", code, self.get_sender_ip()]
        response = make_response(
            render_template(
                "login-page.html", locals=self.locals, url_for=url_for
            )
        )
        response.set_cookie(
            "token",
            connect_code,
            expires=datetime.now(tz=self.timezone) + timedelta(days=3650),
            httponly=False,
            secure=False if getenv("FLASK_ENV") == "development" else True,
            samesite="Lax",
        )
        return response

    @self.route("/login", methods=["GET"])
    def login():
        return redirect(self.discord.config.oauth_url)
