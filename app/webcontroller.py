from flask import Blueprint, render_template, abort
from app.models import Pitch


web_blueprint = Blueprint('web_blueprint', __name__, template_folder='templates')


@web_blueprint.route('/', methods=['GET'])
def index():
    count = Pitch.query.count()
    pitches = Pitch.query.all()
    return render_template('index.html', count=count, pitches=pitches)
