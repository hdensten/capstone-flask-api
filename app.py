# todo
# password didn't hash

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_marshmallow import Marshmallow
import os
import bcrypt

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
  password_hash = db.Column(db.String(100), nullable=False)
  movies = db.relationship('Movie', backref='user', lazy=True) ## LOOK INTO LAZY, MIGHT NEED SOMETHING DIFFERENT
  
  # def set_password(self, password):
  #   self.password_hash = bcrypt.hashpw(password, bcrypt.gensalt())
  
  # def check_password(self, password):
  #   return bcrypt.checkpw(password, self.password_hash)

  def __init__(self, username, email, password_hash):
    self.username = username
    self.email = email
    self.password_hash = password_hash

class UserSchema(ma.Schema):
  class Meta:
    fields = ('id', 'username', 'email', 'password_hash')

user_schema = UserSchema()

class Movie(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  tmdb_id = db.Column(db.Integer, unique=True, nullable=False)
  date = db.Column(db.DateTime, nullable=False)
  rating = db.Column(db.Integer, nullable=False)
  review = db.Column(db.Text)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

  def __init__(self, tmdb_id, date, rating, review, user_id):
    self.tmdb_id = tmdb_id
    self.date = date
    self.rating = rating
    self.review = review
    self.user_id = user_id

class MovieSchema(ma.Schema):
  class Meta:
    fields = ('id', 'tmdb_id', 'date', 'rating', 'review', 'user_id')

movie_schema = MovieSchema()
movies_schema = MovieSchema(many=True)

class Session(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(100))
  session = db.Column(db.String(100))

  def __init__(self, username, session):
    self.username = username
    self.session = session

class SessionSchema(ma.Schema):
  class Meta:
    fields = ('id','username', 'session')

session_schema = SessionSchema()

@app.route('/user/register', methods=["POST"])
def register():
  username = request.json['username']
  email = request.json['email']
  password = request.json['password']

  password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

  new_user = User(username, email, password_hash.decode('utf-8'))

  db.session.add(new_user)
  db.session.commit()

  user = User.query.get(new_user.id)

  return user_schema.jsonify(user)

@app.route('/user/login', methods=["GET", "POST"])
def login():
  username = request.json['username']
  password = request.json['password']

  user = User.query.filter_by(username=username).first()

  if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
    return user_schema.jsonify(user)
  else:
    return 400

# @app.route('/user/logout')
# def logout():
#   return "NOT_LOGGED_IN"

@app.route('/movies/<userid>', methods=["GET"])
def get_movies(userid):
  movies = Movie.query.filter_by(user_id=userid).order_by(Movie.date).all()
  result = movies_schema.dump(movies)
  return jsonify(result)

@app.route('/movie/<userid>/<movieid>', methods=["GET"])
def get_movie(userid, movieid):
  all_movies = Movie.query.filter_by(user_id=userid).all()
  movie = all_movies.get(movieid)
  return movie_schema.jsonify(movie)

@app.route('/movie', methods=["POST"])
def add_movie():
  tmdb_id = request.json['tmdb_id']
  date = request.json['date']
  rating = request.json['rating']
  review = request.json['review']
  user_id = request.json['user_id']

  new_movie = Movie(tmdb_id, date, rating, review, user_id)

  db.session.add(new_movie)
  db.session.commit()

  movie = Movie.query.get(new_movie.id)

  return movie_schema.jsonify(movie)

@app.route('/movie/<userid>/<movieid>', methods=['DELETE'])
def delete_movie(movieid):
  all_movies = Movie.query.filter_by(user_id=userid).all()
  movie = all_movies.get(movieid)

  db.session.delete(movie)
  db.session.commit()

  return "RECORD DELETED"


@app.route('/session/new', methods=['POST'])
def new_session():
  username = request.json['username']
  session = request.json['session']

  new_session = Session(username, session)

  session = Session.query.get(new_session.session)

  return session_schema.jsonify(session)

@app.route('/session/<sessionid>', methods=['GET'])
def get_session(sessionid):
  session = Session.query.get(sessionid)
  return session_schema.jsonify(session)

@app.route('/session/logout/<sessionid>', methods=['DELETE'])
def logout(sessionid):
  session = Session.query.get(sessionid)
  db.session.delete(session)
  db.session.commit()

  return 200

@app.route('/session/users', methods=['POST'])
def get_user():
  username = request.json['username']
  user = User.query.get(username)
  return user_schema.jsonify(user)


if __name__ == '__main__':
  app.run(debug=True)
