from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

webapp = Flask(__name__)
webapp.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///db.sqlite3"
webapp.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(webapp)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=False)
    message = db.Column(db.String, unique=False)


db.create_all()


@webapp.route("/", methods=["GET", "POST"])
def index():
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

    return render_template("index.html", username=username, messages=messages)


@webapp.route("/delete", methods=["GET"])
def delete():
    message_id = request.args.get("id")

    print("delete {}".format(message_id))

    db.session.query(Message).filter(Message.id == message_id).delete()
    db.session.commit()

    username = request.args.get("username")
    messages = Message.query.all()

    return render_template("index.html", username=username, messages=messages)

if __name__ == "__main__":
    webapp.run(use_reloader=True)