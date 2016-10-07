from flask import current_app
import uuid
import boto
from boto.s3.key import Key
from app.models import db

def get_bucket():
    conn = boto.connect_s3()
    try:
        bucket = conn.get_bucket(current_app.config.get('AWS_BUCKET_NAME'))
    except Exception:
        bucket = conn.create_bucket(current_app.config.get('AWS_BUCKET_NAME'))
    return bucket

def store(key, data, bucket=None, type=None):
    if not bucket:
        bucket = get_bucket()
    k = Key(bucket)
    k.key = key
    headers = {}
    if type:
        headers['Content-Type'] = type
    try:
        k.set_contents_from_string(data, headers=headers)
    except:
        k.set_contents_from_string(data.read(), headers=headers)
    k.make_public()
    return k

def store_video(video):
    from app.models import Video
    key_base = str(uuid.uuid4())
    bucket = get_bucket()
    store(key_base, video, bucket=bucket, type='video/quicktime')
    url = "http://s3-us-west-1.amazonaws.com/%s/%s" % (current_app.config.get('AWS_BUCKET_NAME'), key_base)
    video_m = Video(
        url=url,
    )
    db.session.add(video_m)
    db.session.commit()
    return video_m

def store_video_url(video_url):
    from app.models import Video
    video_m = Video(
        url=video_url,
    )
    db.session.add(video_m)
    db.session.commit()
    return video_url
