from flask import Flask, render_template
from config import config
from flask_sqlalchemy import Model, SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from werkzeug.exceptions import HTTPException


class BaseModel(Model):
    def to_json(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


db = SQLAlchemy(model_class=BaseModel)

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    db.init_app(app)
    app.secret_key = 'super secret string'
    return app

app = create_app('testing')

bcrypt = Bcrypt(app)  # Create/Check hashpassword
migrate = Migrate(app, db)



@app.errorhandler(404)
def server_error(error):
    return render_template('404.html'), 404


@app.errorhandler(Exception)
def server_error(e):
    if isinstance(e, HTTPException):
        return e
    return render_template('404.html'), 404


from server.controller import controller, api











