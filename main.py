from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime, time, timedelta
import os.path
import json
import re
import os

# loading configurations
with open("config.json", "r") as configfile:
    config = json.load(configfile)
    parameters = config["parameters"]
    services = config["services"]


# Add a new url to sitemap , takes whole url as input (example : add_sitemap("abc.example.com/blogs/new-blog"))
def add_sitemap(site_url):
    with open("templates/sitemap.xml", "r") as sitemap_file:
        initial_sitemap = sitemap_file.read()
    with open("templates/sitemap.xml", "w") as sitemap_file:
        new_site_url = f"<url>\n<loc>http://{site_url}</loc>\n<lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>\n</url>\n\n<url>\n<loc>https://{site_url}</loc>\n<lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>\n</url>\n"
        sitemap_file.write(
            f"{initial_sitemap.split('</urlset>')[0]}\n{new_site_url}\n</urlset>\n"
        )


# initial configuration of sitemap
def sitemap_init():
    with open("templates/sitemap.xml", "w") as sitemap_file:
        date = datetime.now().strftime("%Y-%m-%d")
        sitemap_file.write(
            f"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n<url>\n  <loc>http://{parameters['WEBSITE_ADDR']}/</loc>\n  <lastmod>{date}</lastmod>\n</url>\n<url>\n  <loc>http://{parameters['WEBSITE_ADDR']}/signin</loc>\n  <lastmod>{date}</lastmod>\n</url>\n<url>\n  <loc>http://{parameters['WEBSITE_ADDR']}/login</loc>\n  <lastmod>{date}</lastmod>\n</url>\n<url>\n  <loc>http://{parameters['WEBSITE_ADDR']}/blogs</loc>\n  <lastmod>{date}</lastmod>\n</url>\n<url>\n  <loc>http://{parameters['WEBSITE_ADDR']}/contact</loc>\n  <lastmod>{date}</lastmod>\n</url>\n<url>\n  <loc>http://{parameters['WEBSITE_ADDR']}/aboutme</loc>\n  <lastmod>{date}</lastmod>\n</url>         \n<url>\n  <loc>https://{parameters['WEBSITE_ADDR']}/</loc>\n  <lastmod>{date}</lastmod>\n</url>\n<url>\n  <loc>https://{parameters['WEBSITE_ADDR']}/signin</loc>\n  <lastmod>{date}</lastmod>\n</url>\n<url>\n  <loc>https://{parameters['WEBSITE_ADDR']}/login</loc>\n  <lastmod>{date}</lastmod>\n</url>\n<url>\n  <loc>https://{parameters['WEBSITE_ADDR']}/blogs</loc>\n  <lastmod>{date}</lastmod>\n</url>\n<url>\n  <loc>https://{parameters['WEBSITE_ADDR']}/contact</loc>\n  <lastmod>{date}</lastmod>\n</url>\n<url>\n  <loc>https://{parameters['WEBSITE_ADDR']}/aboutme</loc>\n  <lastmod>{date}</lastmod>\n</url>\n</urlset>"
        )

    # adding services and projects to sitemap
    for freelancing in services["allfreelancing"]:
        add_sitemap(f'{parameters["WEBSITE_ADDR"]}/freelencing/{freelancing}')

    for projects in services["allprojects"]:
        add_sitemap(f'{parameters["WEBSITE_ADDR"]}/projects/{projects}')


# configuring flask
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = parameters["server_uri"]
app.config["SECRET_KEY"] = "#$234fsgj@!#4ldjas"
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
app.config["UPLOAD_FOLDER"] = parameters["UPLOAD_FOLDER"]
app.config["MEDIA_UPLOAD_FOLDER"] = parameters["MEDIA_UPLOAD_FOLDER"]
sitemap_init()


# database classes
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.VARCHAR(20), nullable=False, unique=True)
    email = db.Column(db.VARCHAR(50), nullable=False, unique=True)
    password = db.Column(db.VARCHAR(72), nullable=False)


class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.VARCHAR(20), nullable=False)
    email = db.Column(db.VARCHAR(50), nullable=False)
    title = db.Column(db.VARCHAR(100), nullable=False)
    message = db.Column(db.VARCHAR(1000), nullable=False)
    date = db.Column(db.DateTime, default=datetime.now())
    responded = db.Column(db.BOOLEAN, default=0)


class Blogs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.VARCHAR(1000), nullable=False, unique=True)
    title = db.Column(db.VARCHAR(1000), nullable=False, unique=True)
    filename = db.Column(db.VARCHAR(200), nullable=False, unique=True)
    date = db.Column(db.DateTime, default=datetime.now())


@app.context_processor
def inject_menu():
    return dict(parameters=parameters)


@app.route("/")
def home():
    return render_template(
        "index.html", services=services, allblogs=Blogs.query.all()[::-1]
    )


@app.route("/aboutme")
def aboutme():
    age_time = datetime.now() - datetime(2009, 1, 8, 10, 23, 23)
    days = age_time.days
    years = int(days / 365)
    months = int((days % 365) / 30.2)
    days = int((days % 365) % 30.2)
    return render_template(
        "aboutme.html",
        age_time=f"{years} years, {months} months, {days} days Old",
    )


@app.route("/blogs")
def blogspage():
    return render_template("blogs.html", allblogs=Blogs.query.all()[::-1])


@app.route("/blogs/<string:slug>")
def blog(slug):
    thisblog = Blogs.query.filter_by(slug=slug).first()
    if thisblog:
        return render_template("/blogs/" + thisblog.filename)
    else:
        flash("Blog Does Not Exists !", "error")
        return redirect("/")


@app.route("/signin", methods=["GET", "POST"])
def signin():
    msg = ""
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        user = Users(
            username=username,
            email=email,
            password=bcrypt.generate_password_hash(password),
        )
        if Users.query.filter_by(username=username).first():
            msg = "Username already exists !"
        elif Users.query.filter_by(email=email).first():
            msg = "Email already exists !"
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            msg = "Invalid email address !"
        elif not re.match(r"[A-Za-z0-9]+", username):
            msg = "Username must contain only characters and numbers !"
        elif len(username) > 20:
            msg = "Username must contain less than 20 characters !"
        elif len(email) > 50:
            msg = "Email must contain less than 50 characters !"
        elif len(password) > 20:
            msg = "Passaword must contain less than 20 characters !"
        elif not username or not password or not email:
            msg = "Please fill out the form !"
        else:
            db.session.add(user)
            db.session.commit()
            session["loggedin"] = True
            session["id"] = user.id
            session["username"] = user.username
            session["email"] = user.email
            flash("Successfully SignedIn !", "success")
            return redirect("/")
    flash(msg, "error")
    return render_template("signin.html", msg=msg)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = Users.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session["loggedin"] = True
            session["id"] = user.id
            session["username"] = user.username
            session["email"] = user.email
            flash("Successfully LogedIn !", "success")
            return redirect("/")
        else:
            flash("Invalid Username or Password !", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    if ("loggedin" in session) and session["loggedin"]:
        session.pop("loggedin", None)
        session.pop("id", None)
        session.pop("username", None)
        session.pop("email", None)
        flash("You Logged Out !", "success")
    return redirect("/")


@app.route("/freelancing/<string:servicelink>")
def freelancingservice(servicelink):
    if servicelink in services["allfreelancing"]:
        return render_template(
            "service.html",
            service=services["freelancing"][
                services["allfreelancing"].index(servicelink)
            ],
        )
    else:
        flash("THIS SERVICE DOSE NOT EXISTS !", "success")
        return redirect("/")


@app.route("/projects/<string:servicelink>")
def projectsservice(servicelink):
    if servicelink in services["allprojects"]:
        return render_template(
            "service.html",
            service=services["projects"][services["allprojects"].index(servicelink)],
        )
    else:
        flash("THIS SERVICE DOSE NOT EXISTS !", "success")
        return redirect("/")


@app.route("/contact", methods=["GET", "POST"])
def contactpage():
    msg = ""
    if request.method == "POST":
        if ("loggedin" in session) and session["loggedin"]:
            username = session["username"]
            email = session["email"]
            title = request.form.get("title")
            message = request.form.get("message")
            if len(title) > 100:
                msg = "Title length should be less than 100 !"
            elif len(message) > 1000:
                msg = "Message length should be less than 1000 !"
            else:
                contactform = Contact(
                    username=username, email=email, title=title, message=message
                )
                db.session.add(contactform)
                db.session.commit()
                flash("Contact request sent successfully !", "success")
                return redirect("/")
        else:
            msg = "Please Log In to send Contact Request !"
    if msg != "":
        flash(msg, "error")
    return render_template("contact.html")


@app.route("/editblogs", methods=["GET", "POST"])
def editblogs():
    allblogs = Blogs.query.all()[::-1]
    if (
        ("loggedin" in session)
        and session["loggedin"]
        and session["username"] == parameters["adminname"]
    ):
        if request.method == "POST":

            html_file = request.files["html_file"]
            media_file = request.files["media_file"]
            if ("html_file" not in request.files) and (
                "media_file" not in request.files
            ):
                flash("No file Entered ", "error")
                return render_template("editblogs.html", allblogs=allblogs)
            elif not html_file:
                media_file = request.files["media_file"]
                if media_file and (
                    ("." in media_file.filename)
                    and media_file.filename.rsplit(".", 1)[1].lower()
                    in parameters["ALLOWED_MEDIA"]
                ):
                    filename = secure_filename(media_file.filename)
                    media_file.save(
                        os.path.join(app.config["MEDIA_UPLOAD_FOLDER"], filename)
                    )
                    print("\n\n\nfile uploded \n\n")
                    flash("Media File saved successfully !", "success")
                    return render_template("editblogs.html", allblogs=allblogs)
                else:
                    flash("Please Enter Correct File Extention and Name !", "error")

            elif not media_file:
                html_file = request.files["html_file"]
                if html_file and (
                    ("." in html_file.filename)
                    and html_file.filename.rsplit(".", 1)[1].lower()
                    in parameters["ALLOWED_EXTENSIONS"]
                ):
                    filename = secure_filename(html_file.filename)
                    html_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                    print("\n\n\nfile uploded \n\n")
                    flash("HTML File saved successfully !", "success")
                    return render_template("editblogs.html", allblogs=allblogs)
                else:
                    flash("Please Enter Correct File Extention and Name !", "error")
            else:
                if media_file and (
                    ("." in media_file.filename)
                    and media_file.filename.rsplit(".", 1)[1].lower()
                    in parameters["ALLOWED_MEDIA"]
                ):
                    filename = secure_filename(media_file.filename)
                    media_file.save(
                        os.path.join(app.config["MEDIA_UPLOAD_FOLDER"], filename)
                    )
                else:
                    flash("Please Enter Correct File Extention and Name !", "error")
                if html_file and (
                    ("." in html_file.filename)
                    and html_file.filename.rsplit(".", 1)[1].lower()
                    in parameters["ALLOWED_EXTENSIONS"]
                ):
                    filename = secure_filename(html_file.filename)
                    html_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

                else:
                    flash("Please Enter Correct File Extention and Name !", "error")

                flash("Both File saved successfully !", "success")
                return render_template("editblogs.html", allblogs=allblogs)
        return render_template("editblogs.html", allblogs=allblogs)
    else:
        flash("Only admin can access that page !", "error")
        return redirect("/")


@app.route("/editblogs/<string:blogid>", methods=["GET", "POST"])
def createblog(blogid):
    if (
        ("loggedin" in session)
        and session["loggedin"]
        and session["username"] == parameters["adminname"]
    ):
        if request.method == "POST":
            title = request.form.get("title")
            slug = request.form.get("slug")
            filename = request.form.get("filename")
            if len(title) > 1000:
                flash("Length of Title Cannot be greater than 1000", "error")
            elif len(filename) > 200:
                flash("Length of File Name Cannot be greater than 200", "error")
            elif len(slug) > 1000:
                flash("Length of Slug Cannot be greater than 1000", "error")
            elif not set(slug).issubset(
                {
                    "a",
                    "b",
                    "c",
                    "d",
                    "e",
                    "f",
                    "g",
                    "h",
                    "i",
                    "j",
                    "k",
                    "l",
                    "m",
                    "n",
                    "o",
                    "p",
                    "q",
                    "r",
                    "s",
                    "t",
                    "u",
                    "v",
                    "w",
                    "x",
                    "y",
                    "z",
                    "-",
                }
            ):
                flash("Slug Must contain only lowercase letters and '-' !", "error")
            elif not (("." in filename) and filename.split(".")[1].lower() == "html"):
                flash("File Extention must be HTML !", "error")
            elif not os.path.isfile(
                os.path.join(app.config["UPLOAD_FOLDER"], filename)
            ):
                flash("HTML file doesn't exists ! Plrease Upload the file !", "error")
            elif blogid == "0":
                blog = Blogs(title=title, slug=slug, filename=filename)
                db.session.add(blog)
                db.session.commit()
                add_sitemap(f"{parameters['WEBSITE_ADDR']}/{slug}")
                flash("New Blog Created Sussessfully !", "success")
                return redirect("/editblogs")
            else:
                blog = Blogs.query.get(blogid)
                blog.title = title
                blog.slug = slug
                blog.filename = filename
                db.session.commit()
                flash(
                    "Blog no ("
                    + blogid
                    + ") Edited Sussessfully ! \nPlease update blog url in sitemap file manually !",
                    "success",
                )
                return redirect("/editblogs")
        blog = Blogs.query.get(blogid)
        if blogid == "0":
            blog = Blogs(title="", slug="", filename="")
        else:
            blog = Blogs.query.get(blogid)
        return render_template("blogediting.html", blogid=blogid, blog=blog)
    else:
        flash("Only admin can access that page !", "error")
        return redirect("/")


@app.route("/editblogs/<string:blogid>/delete")
def deleteblog(blogid):
    if (
        ("loggedin" in session)
        and session["loggedin"]
        and session["username"] == parameters["adminname"]
    ):
        db.session.delete(Blogs.query.get(blogid))
        db.session.commit()
        flash("Blog no (" + blogid + ") Deleted Sussessfully !\nPlease remove it's url from sitemap manually !", "success")
        return redirect("/editblogs")
    else:
        flash("Only admin can access that page !", "error")
        return redirect("/")


@app.route("/contactrequests", methods=["GET", "POST"])
def contsctrequests():
    if (
        ("loggedin" in session)
        and session["loggedin"]
        and session["username"] == parameters["adminname"]
    ):
        allcontacts = Contact.query.all()[::-1]
        return render_template("contactrequests.html", allcontacts=allcontacts)
    else:
        flash("Only admin can access that page !", "error")
        return redirect("/")


@app.route("/contactrequests/<string:id>", methods=["GET", "POST"])
def editcontact(id):
    if (
        ("loggedin" in session)
        and session["loggedin"]
        and session["username"] == parameters["adminname"]
    ):
        if request.method == "POST":
            contact = Contact.query.get(id)
            if request.form["submit_button"] == "Responded":
                contact.responded = int(not bool(contact.responded))
                db.session.commit()
                flash("Contact no (" + id + ") Marked as Responded ! ", "success")
                return redirect("/contactrequests")
            elif request.form["submit_button"] == "Delete":
                db.session.delete(contact)
                db.session.commit()
                flash("Contact no (" + id + ") Deleted Sussessfully ! ", "success")
                return redirect("/contactrequests")
        return render_template("editcontact.html", id=id, contact=Contact.query.get(id))
    else:
        flash("Only admin can access that page !", "error")
        return redirect("/")


@app.route("/sitemap")
def sitemap():
    return render_template("sitemap.xml")


if __name__ == "__main__":
    app.run(debug=True)
