import os
from flask import Flask


def create_app(config_override={}):
    app = Flask(__name__)
    from app.controller import api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')
    app.config.from_pyfile('../config.py')

    os.environ["AWS_ACCESS_KEY_ID"] = app.config["AWS_ACCESS_KEY_ID"]
    os.environ["AWS_SECRET_ACCESS_KEY"] = app.config["AWS_SECRET_ACCESS_KEY"]

    from app.models import db
    db.init_app(app)

    return app


