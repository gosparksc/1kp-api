from app.app import create_app
from flask_script import Manager
from app.models import db

app = create_app()

manager = Manager(app)

@manager.command
def setup():
    db.create_all()

if __name__ == "__main__":
    manager.run()
