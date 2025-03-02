import os
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
)
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from werkzeug.security import check_password_hash, generate_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


load_dotenv()
app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "postgresql+psycopg2://{user}:{passwd}@{host}:{port}/{table}".format(
    user=os.getenv("POSTGRES_USER"),
    passwd=os.getenv("POSTGRES_PASSWORD"),
    host=os.getenv("POSTGRES_HOST"),
    port=5432,
    table=os.getenv("POSTGRES_DB"),
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


from app import models  # noqa: E402


def get_user():
    if "user" in session:
        return session["user"]


@app.route("/")
def index():
    msg = None
    if "message" in session:
        msg = session["message"]
        session.pop("message", None)

    return render_template(
        "index.html",
        title="MLH Fellow",
        user=get_user(),
        response=msg,
        url=os.getenv("URL"),
    )


@app.route("/about")
def about():
    return render_template(
        "about.html", title="About", user=get_user(), url=os.getenv("URL")
    )


@app.route("/portfolio")
def portfolio():
    return render_template(
        "portfolio.html", title="Portfolio", user=get_user(), url=os.getenv("URL")
    )


@app.route("/portfolio/<project>")
def portfolio_project(project):
    if project != "website1" and project != "website2":
        return (
            render_template(
                "error.html",
                title="404 - Not Found",
                user=get_user(),
                url=os.getenv("URL"),
            ),
            404,
        )
    else:
        if project == "website1":
            num = 1
            img = url_for("static", filename="img/projects/project-1.png")
        else:
            num = 2
            img = url_for("static", filename="img/projects/project-2.png")

        return render_template(
            "project.html",
            title=f"Portfolio - Website #{num}",
            image=img,
            user=get_user(),
            url=os.getenv("URL"),
        )


@app.route("/resume")
def resume():
    return render_template(
        "resume.html", title="Resume", user=get_user(), url=os.getenv("URL")
    )


@app.route("/contact", methods=["GET", "POST"])
def contact():
    response = None

    if request.method == "POST":
        response = "Your message was sent succesfully!"

        try:
            # HTTP POST Request args
            email_sender = request.form["email"]
            name = request.form["name"]
            subject = request.form["subject"]
            message_content = request.form["message"]

            # Data from env
            email_server = os.environ.get("MAIL_SERVER")
            email_server_port = os.environ.get("MAIL_SMPT_PORT")
            email_username = os.environ.get("MAIL_USERNAME")
            email_password = os.environ.get("MAIL_PASSWORD")
            email_recipent = os.environ.get("MAIL_RECIPENT")

            # Email Data
            msg = MIMEText(
                "Name: "
                + name
                + "\nContact email: "
                + email_sender
                + "\nMessage: "
                + message_content
            )
            msg["Subject"] = subject
            msg["From"] = email_username
            msg["To"] = email_recipent

            server = smtplib.SMTP_SSL(email_server, email_server_port)
            server.login(email_username, email_password)
            server.sendmail(email_username, [email_recipent], msg.as_string())
            server.quit()
        except Exception:
            response = "Sorry, there was an error."

    return render_template(
        "contact.html",
        title="Contact",
        response=response,
        user=get_user(),
        url=os.getenv("URL"),
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    user = get_user()

    if user:
        return render_template(
            "temp.html",
            title="Register",
            response="You're already logged in!",
            user=user,
            url=os.getenv("URL"),
        )

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        password2 = request.form.get("password2")

        try:
            if not username:
                error = "Username is required."
            elif not password:
                error = "Password is required."
            elif (
                db.session.query(models.User).filter_by(username=username).first()
                is not None
            ):
                error = f"Username {username} has been taken."
            elif password != password2:
                error = "Passwords don't match."
            elif len(password) < 6:
                error = "Password is too short."
        except Exception:
            error = "Sorry, an error occurred."

        if error is None:
            new_user = models.User(username, generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()

            response = f"User {username} created successfully"
            session["user"] = username

            return render_template(
                "temp.html",
                title="Register",
                response=response,
                user=session["user"],
                url=os.getenv("URL"),
            )

    return render_template(
        "register.html", title="Register", response=error, url=os.getenv("URL")
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    user = get_user()

    if user:
        return render_template(
            "temp.html",
            title="Login",
            response="You're already logged in!",
            user=user,
            url=os.getenv("URL"),
        )

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        try:
            user = db.session.query(models.User).filter_by(username=username).first()

            if user is None:
                error = "Incorrect username."
            elif not check_password_hash(user.password, password):
                error = "Incorrect password."
        except Exception:
            error = "Sorry, an error occurred."

        if error is None:
            response = "Login Successful"
            session["user"] = username

            return render_template(
                "temp.html",
                title="Login",
                response=response,
                user=session["user"],
                url=os.getenv("URL"),
            )

    return render_template(
        "login.html", title="Login", response=error, url=os.getenv("URL")
    )


@app.route("/logout")
def logout():
    if "user" in session:
        session.pop("user", None)
        session["message"] = "You have been successfully logged out."

    return redirect(url_for("index"))


@app.route("/health")
def health():
    return "<p>works</p>"


@app.errorhandler(404)
def page_not_found(e):
    return (
        render_template(
            "error.html",
            title="404 - Not Found",
            user=get_user(),
            url=os.getenv("URL"),
        ),
        404,
    )
