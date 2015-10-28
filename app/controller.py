import datetime

from flask import request, jsonify, Blueprint, current_app, abort
from functools import wraps
from models import Pitch, PitchForm, db
import utils

def auth_token_required(fn):
    @wraps(fn)
    def decorated(*args, **kwargs):
        if request.headers.get('Authorization-Token', '') == current_app.config.get('AUTHENTICATION_TOKEN'):
            return fn(*args, **kwargs)
        return abort(401)
    return decorated

api_blueprint = Blueprint('api_blueprint', __name__)

"""
    Video:
        POST /upload-video --> Uploads video
"""
@api_blueprint.route('/upload-video', methods=['POST', 'GET'])
@auth_token_required
def from_video():
    if request.method == 'POST':
        file = request.files['file']
        video_m = utils.store_video(file.stream)
        rv = {
            'status':'success',
            'video_url': video_m.url
        }
        return jsonify(rv)
    elif current_app.config['DEBUG']:
        return '''
           <!doctype html>
            <title>Upload new File</title>
           <h1>Upload new File</h1>
           <form action="" method=post enctype=multipart/form-data>
             <p><input type=file name=file>
                <input type=submit value=Upload>
           </form>
           '''
    else:
        return abort(404)

"""
    Pitches:
        POST /pitch  --> Creates Pitch
        GET /pitch-view --> Grabs pitches
        GET /pitch-download --> Grabs pitches and marks as downloaded
"""
@api_blueprint.route('/pitch', methods=['POST'])
@auth_token_required
def pitch():

    pitch = Pitch()
    input_data = request.get_json(force=True)
    if not isinstance(input_data, dict):
        return jsonify(status='failure', error='Request data must be a JSON Object', errors=[]), 400


    # validate json user input using WTForms-JSON
    form = PitchForm.from_json(input_data)
    if not form.validate():
        return jsonify(errors=form.errors, status='failure', error='Invalid data'), 400

    # update user in database
    pitch.set_columns(**form.patch_data)
    db.session.add(pitch)
    db.session.commit()

    return jsonify({'status':'success'})


@api_blueprint.route('/pitch-download', methods=['GET'])
@auth_token_required
def pitch_download():
    pitches = Pitch.query.filter(Pitch.downloaded==False).all()
    json_pitches = [pitch.to_dict(show_all=True) for pitch in pitches]

    if request.headers.getlist("X-Forwarded-For"):
        user_ip_addr = request.headers.getlist("X-Forwarded-For")[0]
    else:
        user_ip_addr = request.remote_addr

    for pitch in pitches:
        pitch.downloaded = True
        pitch.downloader_ip = user_ip_addr
        pitch.downloaded_date = datetime.datetime.utcnow()
        db.session.add(pitch)
    db.session.commit()

    return jsonify({'pitches': json_pitches})

@api_blueprint.route('/pitch-view', methods=['GET'])
@auth_token_required
def pitch_view():
    pitches = Pitch.query
    if request.args.get('filter-dl', '') != '':
        pitches = pitches.filter(Pitches.downloaded==False)
    pitches = pitches.all()
    json_pitches = [pitch.to_dict(show_all=True) for pitch in pitches]
    return jsonify({'pitches': json_pitches})
