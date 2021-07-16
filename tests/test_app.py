from app import app, db
from app.models import User
import pytest
from pathlib import Path
from werkzeug.security import generate_password_hash
from flask import session


TEST_DB = "test.db"


@pytest.fixture
def client():
    BASE_DIR = Path(__file__).resolve().parent.parent
    app.config["TESTING"] = True
    app.config["DATABASE"] = BASE_DIR.joinpath(TEST_DB)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{BASE_DIR.joinpath(TEST_DB)}"

    db.create_all()  # setup
    yield app.test_client()  # tests run here
    db.session.remove()
    db.drop_all()  # teardown


@pytest.mark.parametrize(
    argnames=["endpoint", "status", "text"],
    argvalues=[
        ("/", 200, b"MLH Fellow"),
        ("/about", 200, b"About Me"),
        ("/portfolio", 200, b"Website #"),
        ("/portfolio/website1", 200, b"Website #1"),
        ("/portfolio/website2", 200, b"Website #2"),
        ("/resume", 200, b"iframe"),
        ("/contact", 200, b"Want to get in touch? Send me a message:"),
        ("/register", 200, b"Password"),
        ("/login", 200, b"Password"),
        ("/logout", 302, b"/"),
    ],
)
def test_endpoint(client, endpoint, status, text):
    response = client.get(endpoint, content_type="html/text")
    assert response.status_code == status
    assert text in response.data


@pytest.mark.parametrize(
    ["user", "passwd", "passwd2", "result", "text"],
    [
        ("admin", "admin", "admin", False, b"Username admin has been taken"),
        ("admin", "newpass", "newpass", False, b"Username admin has been taken"),
        ("newuser", "admin", "admin", False, b"Password is too short"),
        ("newuser", "admin", "newpass", False, b"t match"),
        ("newuser", "newpass", "newpass", True, b"User newuser created successfully"),
    ],
)
def test_register(client, user, passwd, passwd2, result, text):
    existing_user = User("admin", generate_password_hash("admin"))
    db.session.add(existing_user)

    with client:
        response = client.post(
            "/register",
            data={"username": user, "password": passwd, "password2": passwd2},
        )
        assert response.status_code == 200
        assert text in response.data
        check1 = bytes(f"Hi, {user}!", encoding="utf-8") in response.data
        assert check1 == result
        check2 = "user" in session
        assert check2 == result


@pytest.mark.parametrize(
    ["user", "passwd", "result", "text"],
    [
        ("admin", "admin", True, b"Login Successful"),
        ("admin", "badpass", False, b"Incorrect password"),
        ("baduser", "admin", False, b"Incorrect username"),
        ("baduser", "badpass", False, b"Incorrect username"),
    ],
)
def test_login(client, user, passwd, result, text):
    existing_user = User("admin", generate_password_hash("admin"))
    db.session.add(existing_user)

    with client:
        response = client.post("/login", data={"username": user, "password": passwd})
        assert response.status_code == 200
        assert text in response.data
        check1 = bytes(f"Hi, {user}!", encoding="utf-8") in response.data
        assert check1 == result
        check2 = "user" in session
        assert check2 == result


# checks logout function from logged in user
def test_logout_success(client):
    data = {"username": "admin", "password": "password", "password2": "password"}
    with client:
        client.post("/register", data=data)
        response = client.get("/logout")
        assert response.status_code == 302
        assert "user" not in session
        assert "message" in session


# checks logout function without login
def test_logout_fail(client):
    with client:
        response = client.get("/logout")
        assert response.status_code == 302
        assert "user" not in session
        assert "message" not in session


# checks that passwords are not saved plain text
def test_password_hash(client):
    client.post(
        "/register",
        data={"username": "admin", "password": "password", "password2": "password"},
    )
    passwd = db.session.query(User).filter_by(username="admin").first()
    assert passwd.password != "password"


# checks that creating a user works correctly
def test_new_user():
    user = User("admin", "admin")
    assert user.username == "admin"
    assert user.password == "admin"
