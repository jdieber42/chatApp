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
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    deleted = db.Column(db.Boolean, nullable=False)
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
        return render_template("index.html", error="Wrong username/password!")

    if user_model.deleted:
        return render_template("index.html", error="No active user!")

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
    if not session_token:
        return render_template("index.html", error="User is not logged in!")

    response = make_response(render_template("index.html"))
    if session_token:
        response.set_cookie("session_token", "")

    return response


@webapp.route("/message", methods=["GET", "POST"])
def chat():
    user_model = check_user(request)
    if not user_model:
        return render_template("index.html", error="User is not logged in!")

    if request.method == "POST":
        message = request.form.get("message")

        message_model = Message(user_id=user_model.id, message=message)

        db.session.add(message_model)
        db.session.commit()

    messages = Message.query.all()

    return render_template("chat.html", username=user_model.username, messages=messages)


@webapp.route("/message/delete/<message_id>", methods=["GET"])
def delete(message_id):
    user_model = check_user(request)
    if not user_model:
        return render_template("index.html", error="User is not logged in!")

    print("delete {}".format(message_id))

    message_model = db.session.query(Message).filter(Message.id == int(message_id)).first()

    if message_model in user_model.messages:
        db.session.delete(message_model)
        db.session.commit()

    messages = Message.query.all()

    return render_template("chat.html", username=user_model.username, messages=messages)


@webapp.route("/profile", methods=["GET"])
def profile():
    user_model = check_user(request)
    if not user_model:
        return render_template("index.html", error="User is not logged in!")

    return render_template("profile.html", user=user_model)


@webapp.route("/profile/create", methods=["GET", "POST"])
def profile_create():
    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username")

    email = request.form.get("email")

    password = request.form.get("password")
    password_again = request.form.get("password_again")

    if password != password_again:
        return render_template("register.html", error="Password and password again must match!")

    user_model = db.session.query(User).filter(User.username == username).first()
    if user_model:
        return render_template("register.html", error="Username is already used!")

    user_model = User(username=username, deleted=False, email=email,
                      password=hashlib.sha256(password.encode()).hexdigest())
    db.session.add(user_model)
    db.session.commit()

    return render_template("index.html")


@webapp.route("/profile/edit", methods=["GET", "POST"])
def profile_edit():
    user_model = check_user(request)
    if not user_model:
        return render_template("index.html", error="User is not logged in!")

    if request.method == "POST":
        user_model.username = request.form.get("username")
        user_model.email = request.form.get("email")

        db.session.add(user_model)
        db.session.commit()

        return render_template("profile.html", user=user_model)
    else:
        return render_template("profile_edit.html", user=user_model)


@webapp.route("/profile/delete", methods=["GET"])
def profile_delete():
    user_model = check_user(request)
    if not user_model:
        return render_template("index.html", error="User is not logged in!")

    user_model.deleted = True
    db.session.add(user_model)
    db.session.commit()

    return render_template("index.html")


@webapp.route("/user", methods=["GET"])
def user():
    user_model = check_user(request)
    if not user_model:
        return render_template("index.html", error="User is not logged in!")

    users = User.query.all()

    return render_template("user.html", user=user_model, users=users)


@webapp.route("/user/<user_id>", methods=["GET"])
def user_edit(user_id):
    user_model = check_user(request)
    if not user_model:
        return render_template("index.html", error="User is not logged in!")

    user_model_details = db.session.query(User).filter(User.id == int(user_id)).one()

    return render_template("user_details.html", user=user_model, user_details=user_model_details)


def check_session(request):
    session_token = request.cookies.get("session_token")
    if not session_token:
        return None
    return session_token


def check_user(request):
    session_token = check_session(request)
    if not session_token:
        return None

    user_model = db.session.query(User).filter(User.session_token == session_token).one()
    if user_model.deleted:
        return None
    return user_model


if __name__ == "__main__":
    webapp.run(use_reloader=True)