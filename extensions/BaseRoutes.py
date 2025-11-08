from flask import send_from_directory, Response
from os import path

def setup(self):
    @self.route("/favicon.ico")
    def favicon():
        root_path = path.join(self.root_path, "static")
        return send_from_directory(
            path.join(root_path, "icons"),
            "favicon.ico",
            mimetype="image/vnd.microsoft.icon",
        )
        
    @self.route("/robots.txt")
    def robots_txt():
        default_robots = """User-agent: *
Allow: /
Disallow: /api/
Disallow: /connect/
"""
        return Response(default_robots, mimetype="text/plain")

