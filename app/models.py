from flask.ext.sqlalchemy import SQLAlchemy
from flask import request

import uuid
import wtforms_json
from sqlalchemy import not_, func
from sqlalchemy.dialects.postgresql import UUID
from wtforms import Form
from wtforms.fields import FormField, FieldList, StringField, SelectField
from wtforms.validators import Length, Required

from flask import current_app as app
from flask import request, json, jsonify, abort
from flask.ext.sqlalchemy import SQLAlchemy

from datetime import datetime

db = SQLAlchemy()

def set_default_device_id():
    if request is not None:
        return request.headers.get('DEVICE-ID', None)
    return None

# db = SQLAlchemy(app)
wtforms_json.init()

class Model(db.Model):
    """Base SQLAlchemy Model for automatic serialization and
    deserialization of columns and nested relationships.
    https://gist.github.com/alanhamlett/6604662
    Usage::
        >>> class User(Model):
        >>>     id = db.Column(db.Integer(), primary_key=True)
        >>>     email = db.Column(db.String(), index=True)
        >>>     name = db.Column(db.String())
        >>>     password = db.Column(db.String())
        >>>     posts = db.relationship('Post', backref='user', lazy='dynamic')
        >>>     ...
        >>>     default_fields = ['email', 'name']
        >>>     hidden_fields = ['password']
        >>>     readonly_fields = ['email', 'password']
        >>>
        >>> class Post(Model):
        >>>     id = db.Column(db.Integer(), primary_key=True)
        >>>     user_id = db.Column(db.String(), db.ForeignKey('user.id'), nullable=False)
        >>>     title = db.Column(db.String())
        >>>     ...
        >>>     default_fields = ['title']
        >>>     readonly_fields = ['user_id']
        >>>
        >>> model = User(email='john@localhost')
        >>> db.session.add(model)
        >>> db.session.commit()
        >>>
        >>> # update name and create a new post
        >>> validated_input = {'name': 'John', 'posts': [{'title':'My First Post'}]}
        >>> model.set_columns(**validated_input)
        >>> db.session.commit()
        >>>
        >>> print(model.to_dict(show=['password', 'posts']))
        >>> {u'email': u'john@localhost', u'posts': [{u'id': 1, u'title': u'My First Post'}], u'name': u'John', u'id': 1}
    """
    __abstract__ = True

    # Stores changes made to this model's attributes. Can be retrieved
    # with model.changes
    _changes = {}

    def __init__(self, **kwargs):
        kwargs['_force'] = True
        self._set_columns(**kwargs)

    def _set_columns(self, **kwargs):
        force = kwargs.get('_force')

        readonly = []
        if hasattr(self, 'readonly_fields'):
            readonly = self.readonly_fields
        if hasattr(self, 'hidden_fields'):
            readonly += self.hidden_fields

        readonly += [
            'id',
            'created',
            'updated',
            'modified',
            'created_at',
            'updated_at',
            'modified_at',
        ]

        changes = {}

        columns = self.__table__.columns.keys()
        relationships = self.__mapper__.relationships.keys()

        for key in columns:
            allowed = True if force or key not in readonly else False
            exists = True if key in kwargs else False
            if allowed and exists:
                val = getattr(self, key)
                if val != kwargs[key]:
                    changes[key] = {'old': val, 'new': kwargs[key]}
                    setattr(self, key, kwargs[key])

        for rel in relationships:
            allowed = True if force or rel not in readonly else False
            exists = True if rel in kwargs else False
            if allowed and exists:
                is_list = self.__mapper__.relationships[rel].uselist
                if is_list:
                    valid_ids = []
                    query = getattr(self, rel)
                    cls = self.__mapper__.relationships[rel].argument()
                    for item in kwargs[rel]:
                        if 'id' in item and query.filter_by(id=item['id']).limit(1).count() == 1:
                            obj = cls.query.filter_by(id=item['id']).first()
                            col_changes = obj.set_columns(**item)
                            if col_changes:
                                col_changes['id'] = str(item['id'])
                                if rel in changes:
                                    changes[rel].append(col_changes)
                                else:
                                    changes.update({rel: [col_changes]})
                            valid_ids.append(str(item['id']))
                        else:
                            col = cls()
                            col_changes = col.set_columns(**item)
                            query.append(col)
                            db.session.flush()
                            if col_changes:
                                col_changes['id'] = str(col.id)
                                if rel in changes:
                                    changes[rel].append(col_changes)
                                else:
                                    changes.update({rel: [col_changes]})
                            valid_ids.append(str(col.id))

                    # delete related rows that were not in kwargs[rel]
                    for item in query.filter(not_(cls.id.in_(valid_ids))).all():
                        col_changes = {
                            'id': str(item.id),
                            'deleted': True,
                        }
                        if rel in changes:
                            changes[rel].append(col_changes)
                        else:
                            changes.update({rel: [col_changes]})
                        db.session.delete(item)

                else:
                    val = getattr(self, rel)
                    if self.__mapper__.relationships[rel].query_class is not None:
                        if val is not None:
                            col_changes = val.set_columns(**kwargs[rel])
                            if col_changes:
                                changes.update({rel: col_changes})
                    else:
                        if val != kwargs[rel]:
                            setattr(self, rel, kwargs[rel])
                            changes[rel] = {'old': val, 'new': kwargs[rel]}

        return changes

    def set_columns(self, **kwargs):
        self._changes = self._set_columns(**kwargs)
        if 'modified' in self.__table__.columns:
            self.modified = datetime.utcnow()
        if 'updated' in self.__table__.columns:
            self.updated = datetime.utcnow()
        if 'modified_at' in self.__table__.columns:
            self.modified_at = datetime.utcnow()
        if 'updated_at' in self.__table__.columns:
            self.updated_at = datetime.utcnow()
        return self._changes

    @property
    def changes(self):
        return self._changes

    def reset_changes(self):
        self._changes = {}

    def to_dict(self, show=None, hide=None, path=None, show_all=None):
        """ Return a dictionary representation of this model.
        """

        if not show:
            show = []
        if not hide:
            hide = []
        hidden = []
        if hasattr(self, 'hidden_fields'):
            hidden = self.hidden_fields
        default = []
        if hasattr(self, 'default_fields'):
            default = self.default_fields

        ret_data = {}

        if not path:
            path = self.__tablename__.lower()
            def prepend_path(item):
                item = item.lower()
                if item.split('.', 1)[0] == path:
                    return item
                if len(item) == 0:
                    return item
                if item[0] != '.':
                    item = '.%s' % item
                item = '%s%s' % (path, item)
                return item
            show[:] = [prepend_path(x) for x in show]
            hide[:] = [prepend_path(x) for x in hide]

        columns = self.__table__.columns.keys()
        relationships = self.__mapper__.relationships.keys()
        properties = dir(self)

        for key in columns:
            check = '%s.%s' % (path, key)
            if check in hide or key in hidden:
                continue
            if show_all or key is 'id' or check in show or key in default:
                ret_data[key] = getattr(self, key)

        for key in relationships:
            check = '%s.%s' % (path, key)
            if check in hide or key in hidden:
                continue
            if show_all or check in show or key in default:
                hide.append(check)
                is_list = self.__mapper__.relationships[key].uselist
                if is_list:
                    ret_data[key] = []
                    for item in getattr(self, key):
                        ret_data[key].append(item.to_dict(
                            show=show,
                            hide=hide,
                            path=('%s.%s' % (path, key.lower())),
                            show_all=show_all,
                        ))
                else:
                    if self.__mapper__.relationships[key].query_class is not None:
                        ret_data[key] = getattr(self, key).to_dict(
                            show=show,
                            hide=hide,
                            path=('%s.%s' % (path, key.lower())),
                            show_all=show_all,
                        )
                    else:
                        ret_data[key] = getattr(self, key)

        for key in list(set(properties) - set(columns) - set(relationships)):
            if key.startswith('_'):
                continue
            check = '%s.%s' % (path, key)
            if check in hide or key in hidden:
                continue
            if show_all or check in show or key in default:
                val = getattr(self, key)
                try:
                    ret_data[key] = json.loads(json.dumps(val))
                except:
                    pass

        return ret_data

class Video(Model):
    __tablename__ = 'video'
    modified = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    created = db.Column(db.DateTime, default=func.now())
    device_id = db.Column(db.String, default=set_default_device_id, nullable=True)
    url = db.Column(db.String, primary_key=True)


class Pitch(Model):
    __tablename__ = 'pitch'
    id = db.Column(db.Integer, primary_key=True)

    modified = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    created = db.Column(db.DateTime, default=func.now())
    device_id = db.Column(db.String, default=set_default_device_id, nullable=True)

    # User Info
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)
    email = db.Column(db.String)
    student_org = db.Column(db.String)
    college = db.Column(db.String)
    grad_year = db.Column(db.String(4))

    # Pitch Info
    pitch_title = db.Column(db.String)
    pitch_category = db.Column(db.String)
    pitch_short_description = db.Column(db.Text)

    # Video Info
    video_url = db.Column(db.String, db.ForeignKey('video.url'), nullable=False)

    # Status
    downloaded = db.Column(db.Boolean, default=False)
    downloader_ip = db.Column(db.String)
    downloaded_date = db.Column(db.DateTime)


class PitchForm(Form):
    first_name = StringField(validators=[Length(max=250), Required()])
    last_name = StringField(validators=[Length(max=250), Required()])
    email = StringField(validators=[Length(max=250), Required()])
    student_org = StringField(validators=[Length(max=250)])
    college = SelectField(validators=[Required()], choices=[('Letters, Arts and Sciences', 'Letters, Arts and Sciences'), ('Accounting', 'Accounting'), ('Architecture', 'Architecture'), ('Business', 'Business'), ('Arts, Technology, Business', 'Arts, Technology, Business'), ('Cinematic Arts', 'Cinematic Arts'), ('Communication', 'Communication'), ('Dramatic Arts', 'Dramatic Arts'), ('Dentistry', 'Dentistry'), ('Education', 'Education'), ('Engineering', 'Engineering'), ('Fine Arts', 'Fine Arts'), ('Gerontology', 'Gerontology'), ('Law', 'Law'), ('Medicine', 'Medicine'), ('Music', 'Music'), ('Pharmacy', 'Pharmacy'), ('Policy, Planning, and Developement', 'Policy, Planning, and Developement'), ('Social Work', 'Social Work')])
    grad_year = StringField(validators=[Length(max=4), Required()])

    pitch_title = StringField(validators=[Length(max=250), Required()])
    pitch_category = SelectField(validators=[Required()], choices=[('Music', 'Music'), ('Film', 'Film'), ('Environment', 'Environment'), ('Education', 'Education'), ('Tech & Hardware', 'Tech & Hardware'), ('Web & Software', 'Web & Software'), ('Consumer Products & Small Business', 'Consumer Products & Small Business'), ('Health', 'Health'), ('University Improvements', 'University Improvements'), ('Mobile', 'Mobile'), ('Research', 'Research'), ('Video Games', 'Video Games')])
    pitch_short_description = StringField(validators=[Length(max=5000), Required()])

    video_url = StringField(validators=[Required()])

    def validate(self):
        rv = Form.validate(self)

        if Video.query.filter(Video.url==self.video_url.data).count() != 1:
            self.video_url.errors.append('Video url not found')
            return False

        if not rv:
            return False

        return True
