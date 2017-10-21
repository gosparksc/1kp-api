from flask import Blueprint, render_template, abort
from app.models import Pitch


web_blueprint = Blueprint('web_blueprint', __name__, template_folder='templates')


@web_blueprint.route('/', methods=['GET'])
def index():
    count = Pitch.query.count() - 13  # Temporary to get the accurate count
    pitches = Pitch.query.all()
    return render_template('index.html', count=count, pitches=pitches)


@web_blueprint.route('/v/<int:video_id>', methods=['GET'])
def v(video_id):
    count = Pitch.query.count() - 13  # Temporary to get the accurate count
    pitch = Pitch.query.filter_by(id=video_id).first()
    return render_template('video.html', count=count, pitch=pitch)
