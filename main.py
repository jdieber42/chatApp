import hashlib
import os
import uuid

from flask import Flask, render_template, request, make_response
from flask_sqlalchemy import SQLAlchemy

webapp = Flask(__name__)
webapp.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///db.sqlite3").replace("postgres://", "postgresql://", 1)
webapp.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(webapp)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=False, nullable=False)
    password = db.Column(db.String, nullable=False)
    messages = db.relationship('Message', backref='user', lazy=True)
    session_token = db.Column(db.String, unique=False)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


db.create_all()


@webapp.route("/", methods=["GET"])
def index():
    username = request.cookies.get("remember_user")

    return render_template("index.html", username=username)


@webapp.route("/login", methods=["Post"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    remember_me = request.form.get("remember")

    user_model = db.session.query(User).filter(User.username == username).first()
    if not user_model:
        user_model = User(username=username, password=hashlib.sha256(password.encode()).hexdigest())
        db.session.add(user_model)
        db.session.commit()

    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    if hashed_password != user_model.password:
        return render_template("index.html", error="Wrong username/password!")
    else:
        session_token = str(uuid.uuid4())

        user_model.session_token = session_token
        db.session.commit()

    messages = Message.query.all()

    response = make_response(render_template("chat.html", username=user_model.username, messages=messages))
    if remember_me:
        response.set_cookie("remember_user", user_model.username)
    else:
        response.set_cookie("remember_user", "")

    response.set_cookie("session_token", session_token, httponly=True, samesite='Strict')

    return response


@webapp.route("/logout", methods=["GET"])
def logout():
    session_token = request.cookies.get("session_token")

    response = make_response(render_template("index.html"))
    if session_token:
        response.set_cookie("session_token", "")

    return response


@webapp.route("/chat", methods=["GET", "POST"])
def chat():
    session_token = request.cookies.get("session_token")
    if not session_token:
        return render_template("index.html", error="User is not logged in!")

    user_model = db.session.query(User).filter(User.session_token == session_token).one()
    if request.method == "POST":
        message = request.form.get("message")

        message_model = Message(user_id=user_model.id, message=message)

        db.session.add(message_model)
        db.session.commit()

    messages = Message.query.all()

    return render_template("chat.html", username=user_model.username, messages=messages)


@webapp.route("/delete", methods=["GET"])
def delete():
    session_token = request.cookies.get("session_token")
    if not session_token:
        return render_template("index.html", error="User is not logged in!")

    message_id = request.args.get("id")

    print("delete {}".format(message_id))

    user_model = db.session.query(User).filter(User.session_token == session_token).one()
    message_model = db.session.query(Message).filter(Message.id == message_id).first()

    if message_model in user_model.messages:
        db.session.delete(message_model)
        db.session.commit()

    messages = Message.query.all()

    return render_template("chat.html", username=user_model.username, messages=messages)

if __name__ == "__main__":
    webapp.run(use_reloader=True)