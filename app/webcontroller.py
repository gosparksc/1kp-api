from flask import Blueprint, render_template, abort
from app.models import Pitch


web_blueprint = Blueprint('web_blueprint', __name__, template_folder='templates')

category_to_url_map = {'Arts, Media & Culture': 'arts',
                       'Community Impact & Education': 'impact-education',
                       'Environment': 'environment',
                       'Health & Biotech': 'health-biotech',
                       'Life Hacks & Other': 'life-hacks',
                       'Politics': 'politics'}


@web_blueprint.route('/', methods=['GET'])
def index():
    count = Pitch.query.count() - 13  # Temporary to get the accurate count
    pitches = Pitch.query.all()
    return render_template('index.html', count=count, pitches=pitches)


@web_blueprint.route('/v/<int:video_id>', methods=['GET'])
def v(video_id):
    count = Pitch.query.count() - 13  # Temporary to get the accurate count
    pitch = Pitch.query.filter_by(id=video_id).first()
    category_url = category_to_url_map[pitch.pitch_category]
    return render_template('video.html', count=count, pitch=pitch, category_url=category_url)


@web_blueprint.route('/c/<string:category_id>', methods=['GET'])
def c(category_id):
    url_to_category_map = {'arts': 'Arts, Media & Culture',
                           'impact-education': 'Community Impact & Education',
                           'environment': 'Environment',
                           'health-biotech': 'Health & Biotech',
                           'life-hacks': 'Life Hacks & Other',
                           'politics': 'Politics'}

    category = url_to_category_map.get(category_id)
    if category is None:
        return abort(404)

    count = Pitch.query.count() - 13  # Temporary to get the accurate count
    pitch = Pitch.query.filter_by(pitch_category=category).all()
    return render_template('index.html', count=count,
                           pitches=pitch, category=category)
