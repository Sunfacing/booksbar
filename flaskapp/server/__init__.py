from flask import Flask
from config import Config
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import Model, SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_bcrypt  import Bcrypt
from flask_migrate import Migrate
from werkzeug.exceptions import HTTPException



class BaseModel(Model):
    def to_json(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app, model_class=BaseModel)
limiter = Limiter(app, key_func=get_remote_address)
bcrypt = Bcrypt(app)  # Create/Check hashpassword
jwt = JWTManager(app) # Generate token
migrate = Migrate(app, db)



@app.errorhandler(404)
def server_error(error):
    return "The page you request is not found", 404



@app.errorhandler(Exception)
def server_error(e):
    if isinstance(e, HTTPException):
        return e
    return "The page you request is not found", 404



from server.controller import user_controller










