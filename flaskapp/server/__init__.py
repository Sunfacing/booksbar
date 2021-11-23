from flask import Flask, render_template
from config import Config
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import Model, SQLAlchemy
from flask_bcrypt  import Bcrypt
from flask_migrate import Migrate
from werkzeug.exceptions import HTTPException



class BaseModel(Model):
    def to_json(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app, model_class=BaseModel)
app.secret_key = 'super secret string'
bcrypt = Bcrypt(app)  # Create/Check hashpassword
jwt = JWTManager(app) # Generate token
migrate = Migrate(app, db)


@app.errorhandler(404)
def server_error(error):
    return render_template('404.html'), 404



@app.errorhandler(Exception)
def server_error(e):
    if isinstance(e, HTTPException):
        return e
    return render_template('404.html'), 404



from server.controller import controller











