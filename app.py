from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_marshmallow import Marshmallow
import os

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
    os.path.join(basedir, 'app.sqlite')

CORS(app)

db = SQLAlchemy(app)
ma = Marshmallow(app)

class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(100), unique=True, nullable=False)
  email = db.Column(db.String(100), unique=True, nullable=False)
  password = db.Column(db.String(100), nullable=False)

  def __init__(self, username, email, password):
    self.username = username
    self.email = email
    self.password = password

class UserSchema(ma.Schema):
  class Meta:
    fields = ('id', 'username', 'email', 'password')

user_schema = UserSchema()

class Movie(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  date = db.Column(db.DateTime, nullable=False)
  rating = db.Column(db.Integer, nullable=False)
  review = db.Column(db.Text)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
