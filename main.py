import os
from flask import Flask, render_template, request, make_response
from flask_sqlalchemy import SQLAlchemy

webapp = Flask(__name__)
webapp.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///db.sqlite3")
webapp.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(webapp)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=False)
    message = db.Column(db.String, unique=False)


db.create_all()


@webapp.route("/", methods=["GET"])
def index():
    username = request.cookies.get("remember_user")

    return render_template("index.html", username=username)


@webapp.route("/login", methods=["Post"])
def login():
    username = request.form.get("username")
    remember_me = request.form.get("remember")

    messages = Message.query.all()
    response = make_response(render_template("chat.html", username=username, messages=messages))
    if remember_me:
        response.set_cookie("remember_user", username)
    else:
        response.set_cookie("remember_user", "")

    return response


@webapp.route("/chat", methods=["GET", "POST"])
def chat():
    username = None
    if request.method == "POST":
        username = request.form.get("username")
        message = request.form.get("message")

        message_model = Message(username=username, message=message)

        db.session.add(message_model)
        db.session.commit()
    else:
        username = request.args.get("username")

    messages = Message.query.all()

    return render_template("chat.html", username=username, messages=messages)


@webapp.route("/delete", methods=["GET"])
def delete():
    message_id = request.args.get("id")

    print("delete {}".format(message_id))

    db.session.query(Message).filter(Message.id == message_id).delete()
    db.session.commit()

    username = request.args.get("username")
    messages = Message.query.all()

    return render_template("chat.html", username=username, messages=messages)

if __name__ == "__main__":
    webapp.run(use_reloader=True)