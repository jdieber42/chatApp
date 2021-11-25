import os
import pytest
import hashlib

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


from main import db, webapp, User


@pytest.fixture
def client():
    client = webapp.test_client()

    cleanup()
    db.create_all()

    yield client


def test_index(client):
    response = client.get("/")

    assert b'Please sign in' in response.data


def test_profile_create(client):
    username = "Test"
    password = "test_pass"
    email = "user@mail.com"

    response = client.post("/profile/create", data={"username": username, "email": email,
                                                    "password": password, "password_again": "test_pass"})

    assert b'Please sign in' in response.data

    user_model = db.session.query(User).filter(User.username == username).first()
    assert user_model
    assert user_model.password != password
    assert user_model.password == hashlib.sha256(password.encode()).hexdigest()
    assert user_model.email == email


def test_login(client):
    username = "Test1"
    password = "test_pass1"

    session_token = get_session(client, username, password)
    assert session_token


def test_user(client):
    session_token = get_session(client, "Test2", "test_pass2")

    response = client.get("/user")

    assert b'User Overview' in response.data


def test_user_not_logged_in(client):
    response = client.get("/user")

    assert b'Please sign in' in response.data


def test_profile(client):
    session_token = get_session(client, "Test3", "test_pass3")

    response = client.get("/profile")

    assert b'Profile' in response.data


def test_profile_not_logged_in(client):
    response = client.get("/profile")

    assert b'Please sign in' in response.data


def get_session(client, username, password):
    user_model = User(username=username, deleted=False, email=username + "mail.com",
                      password=hashlib.sha256(password.encode()).hexdigest())
    db.session.add(user_model)
    db.session.commit()

    response = client.post("/login", data={"username": username, "password": password})

    assert b'Welcome to our Chat App' in response.data

    return extract_session_cookie(response)


def extract_session_cookie(response):
    session_token = None
    for header in response.headers:
        if header[0] == 'Set-Cookie' and 'session_token' in header[1]:
            start_index = header[1].index('=')
            end_index = header[1].index(';')
            session_token = header[1][start_index + 1:end_index]
    return session_token


def cleanup():
    db.drop_all()