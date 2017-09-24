from flask import Blueprint, render_template, abort


web_blueprint = Blueprint('web_blueprint', __name__)

@web_blueprint.route('/')
def hello_world():
    return 'Hello, World!'