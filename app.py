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
  movies = db.relationship('Movie', backref='user', lazy=True) 

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
  tmdb_id = db.Column(db.Integer, nullable=False)
  date = db.Column(db.String(10), nullable=False)
  rating = db.Column(db.Integer, nullable=False)
  review = db.Column(db.Text)
  poster_path = db.Column(db.String(100), nullable=False)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

  def __init__(self, tmdb_id, date, rating, review, poster_path, user_id):
    self.tmdb_id = tmdb_id
    self.date = date
    self.rating = rating
    self.review = review
    self.poster_path = poster_path
    self.user_id = user_id

class MovieSchema(ma.Schema):
  class Meta:
    fields = ('id', 'tmdb_id', 'date', 'rating', 'review', 'poster_path', 'user_id')

movie_schema = MovieSchema()
movies_schema = MovieSchema(many=True)

class Session(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  session = db.Column(db.String(100))

  def __init__(self, session):
    self.session = session

class SessionSchema(ma.Schema):
  class Meta:
    fields = ('id', 'session')

session_schema = SessionSchema()

@app.route('/user/register', methods=["POST"])
def register():
  username = request.json['username']
  email = request.json['email']
  password = request.json['password']

  existing_username = User.query.filter_by(username=username).first()
  existing_email = User.query.filter_by(email=email).first()

  if existing_username:
    return "USERNAME_EXISTS"
  elif existing_email:
    return "EMAIL_EXISTS"
  else:
    password_hash = bcrypt.hashpw(password.encode("utf8"), bcrypt.gensalt())
    new_user = User(username, email, password_hash)

    db.session.add(new_user)
    db.session.commit()

    user = User.query.get(new_user.id)

    return user_schema.jsonify(user)

@app.route('/user/login', methods=["GET", "POST"])
def login():
  username = request.json['username']
  password = request.json['password']

  user = User.query.filter_by(username=username).first()
 
  if user:
    if bcrypt.checkpw(password.encode(), user.password_hash):
      return user_schema.jsonify(user)
    else:
      return "INVALID_LOGIN"
  else:
    return "INVALID_LOGIN"


@app.route('/movies/<userid>', methods=["GET"])
def get_movies(userid):
  movies = Movie.query.filter_by(user_id=userid).all()
  result = movies_schema.dump(movies)
  return jsonify(result)

@app.route('/movie/<userid>/<movieid>', methods=["GET"])
def get_movie(userid, movieid):
  movie = Movie.query.filter_by(user_id=userid).filter_by(id=movieid).first()

  return movie_schema.jsonify(movie)

@app.route('/movie', methods=["POST"])
def add_movie():
  tmdb_id = request.json['tmdbId']
  date = request.json['watchDate']
  rating = request.json['rating']
  review = request.json['review']
  poster_path = request.json['posterPath']
  user_id = request.json['userId']

  existing_movie = Movie.query.filter_by(user_id=user_id).filter_by(tmdb_id=tmdb_id).first()

  if existing_movie:
    return "MOVIE_EXISTS"
  else:
    new_movie = Movie(tmdb_id, date, rating, review, poster_path, user_id)
    db.session.add(new_movie)
    db.session.commit()
    movie = Movie.query.get(new_movie.id)
    return movie_schema.jsonify(movie)

@app.route('/movie/delete/<userid>/<movieid>', methods=['DELETE'])
def delete_movie(userid, movieid):
  movie = Movie.query.filter_by(user_id=userid).filter_by(id=movieid).first()

  db.session.delete(movie)
  db.session.commit()

  return "RECORD DELETED"


@app.route('/session/new', methods=['POST'])
def new_session():
  session = request.json['session']
  new_session = Session(session)

  db.session.add(new_session)
  db.session.commit()

  session = Session.query.get(new_session.session)

  return session_schema.jsonify(session)

@app.route('/session/<sessionid>', methods=['GET'])
def get_session(sessionid):
  session = Session.query.filter_by(session=sessionid).first()
  return session_schema.jsonify(session)

@app.route('/session/logout/<sessionId>', methods=['DELETE'])
def logout(sessionId):
  session = Session.query.filter_by(session=sessionId).first()
  db.session.delete(session)
  db.session.commit()

  return "SESSION_DELETED"

@app.route('/session/users', methods=['POST'])
def get_user():
  username = request.json['username']
  user = User.query.filter_by(username=username).first()
  return user_schema.jsonify(user)



if __name__ == '__main__':
  app.run(debug=True)
