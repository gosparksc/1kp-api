import pytest

import json
# import sys, os
# myPath = os.path.dirname(os.path.abspath(__file__))
# sys.path.insert(0, myPath + '/../')

from app.app import create_app
from app.models import db
from client import Client

@pytest.fixture(scope='function')
def app(request):
    # We add some config overrides specifically for testing. The password
    # hash is changed to plaintext to speed up user creation.
    config_override = {
        'SQLALCHEMY_DATABASE_URI': 'postgresql://postgres:ponder@localhost/onekptesting'
    }
    app = create_app(config_override)

    ctx = app.app_context()
    ctx.push()

    db.app = app
    db.create_all()

    def teardown():
        ctx.pop()
        db.drop_all()

    request.addfinalizer(teardown)

    return app


@pytest.fixture(scope='function')
def client(app):
    return Client(app.test_client(), with_admin=True)


""" Begin Testing """

def test_pitch_posting(app, client):
    from app.models import db, Pitch, Video

    v = Video(url='http://gofuckaduck.com')
    db.session.add(v)
    # db.session.commit()

    pitch_data_input = [
        ({}, 400, 9),
        ({
            'first_name':'Brian',
            'last_name':'Anglin',
            'email':'banglin@usc.edu',
            'student_org':'Spark',
            'college': 'Engineering',
            'grad_year': '2018',
            'pitch_title': 'My Dope Pitch',
            'pitch_category': 'Environment',
            'pitch_short_description': 'Yo this is a dope pitch',
            'video_url':'http://gofuckaduck.com'
        }, 200, 0),
        ({
            'last_name':'Anglin',
            'email':'banglin@usc.edu',
            'student_org':'Spark',
            'college': 'IFuckedUPEngineering',
            'grad_year': '2018',
            'pitch_title': 'My Dope Pitch',
            'pitch_category': 'Environment',
            'pitch_short_description': 'Yo this is a dope pitch',
            'video_url':'notindb'
        }, 400, 3),
    ]


    for pitch in pitch_data_input:
        pitch_resp, status_code = client.post('/api/pitch', data=pitch[0])
        assert status_code == pitch[1]
        if pitch[1] != 200:
            assert len(pitch_resp['errors']) == pitch[2]


    successful_pitches = [x[0] for x in pitch_data_input if x[1] == 200]
    assert Pitch.query.count() == len(successful_pitches)
    for pitch in successful_pitches:
        assert 1 == Pitch.query.filter_by(**dict((x, y) for x, y in pitch.items())).count()



def test_device_id_setting(app, client):
    from app.models import db, Pitch, Video

    v = Video(url='http://gofuckaduck.com')
    db.session.add(v)

    pitch_data = {
        'first_name':'Brian',
        'last_name':'Anglin',
        'email':'banglin@usc.edu',
        'student_org':'Spark',
        'college': 'Engineering',
        'grad_year': '2018',
        'pitch_title': 'My Dope Pitch',
        'pitch_category': 'Environment',
        'pitch_short_description': 'Yo this is a dope pitch',
        'video_url':'http://gofuckaduck.com'
    }


    raw_client = client.client

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'DEVICE-ID': '12345678abcdefg'
    }
    resp = raw_client.post('/api/pitch', data=json.dumps(pitch_data), follow_redirects=True, headers=headers)
    assert resp.status_code == 200

    p = Pitch.query.first()
    assert p.device_id == '12345678abcdefg'


