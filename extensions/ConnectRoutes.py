from flask import render_template, url_for, session
from utils.SanitizeText import sanitize_code

def setup(app):
    @app.get('/linked')
    def linked_route():
        return render_template(
            "linked.html",
            locals=app.locals,
            url_for=url_for
        )

    @app.get('/<string:code>')
    @app.get('/')
    def link_route(code = None):
        code = sanitize_code(code) if code else None
        if code:
            valid = True if app.dbutils.get_helix_id_by_code(code) else False
        else:
            valid = False
        if valid:
            session['helix_code'] = code
        return render_template(
            "link.html",
            locals=app.locals,
            url_for=url_for,
            valid=valid,
            oauth_url=app.discord.config.oauth_url
        )


