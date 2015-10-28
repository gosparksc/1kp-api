from flask import request, jsonify, Blueprint, current_app
from functools import wraps
from models import Pitch, PitchForm, db
import utils

def auth_token_required(fn):
    @wraps(fn)
    def decorated(*args, **kwargs):
        if request.headers.get('AUTH_TOKEN', '') == '':
            return fn(*args, **kwargs)
        return _get_unauthorized_response()
    return decorated

api_blueprint = Blueprint('api_blueprint', __name__)

"""
    /upload
        - pitch
    /pitch
        - first_name, last_name, etc
        - pitch url
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



@api_blueprint.route('/')
def root():
    return 'Hello World!'

@api_blueprint.route('/pitch-download', methods=['GET'])
@auth_token_required
def pitch_download():
    pitches = Pitch.query.all()
    json_pitches = [pitch.to_dict(show_all=True) for pitch in pitches]
    return jsonify({'pitches': json_pitches})

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

