from flask import render_template, url_for
import logging

def setup(self):
    @self.errorhandler(404)
    @self.errorhandler(500)
    @self.errorhandler(429)
    @self.errorhandler(403)
    @self.errorhandler(400)
    @self.get("/error")
    def handle_error(e = None):
        if e:
            logging.error(f"Error occurred: {str(e)}") if e.code != 404 else None
        else:
            e = "Failed to login, Please try again."
        return (
            render_template(
                "error.html", error_message=e, locals=self.locals, url_for=url_for
            ),
            e.code if not type(e) == str else 500,
        )
