from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

# Configure MySQL
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "micropub"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

# Init MySQL
mysql = MySQL(app)


# Define the function to control user roles
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Unauthorized, please login.", "danger")
            return redirect(url_for("login"))
        
    return wrap


# Index
@app.route("/")
def index():
    return render_template("index.html")

# About us
@app.route("/about/")
def about():
    return render_template("about.html")

# Page for all articles route
@app.route("/articles/")
def render_articles():
        # Create cursor
    cur = mysql.connection.cursor()

    # Get articles 
    results = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if results > 0:
        return render_template("articles.html", articles=articles)

    else:
        msg = "Check back later, we shall be publishing new articles soon."
        return render_template("articles.html", msg=msg)

    # Close the connection
    cur.close()

# Article page route
@app.route("/article/<id>/")
def view_article(id):

    # Create a cursor
    cur = mysql.connection.cursor()

    # Querry the database
    results = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    return render_template("article.html", article=article)


# Defining User Registration Form Class inheriting from the Form class imported from WTForms module
class RegistrationForm(Form):
    name = StringField("Name", [validators.Length(min=4, max=50)])
    username = StringField("Username", [validators.Length(min=4, max=25)])
    email = StringField("Email", [validators.Length(min=6, max=50)])
    password = PasswordField("Password", [
        validators.DataRequired(),
        validators.EqualTo("confirm", message="Passwords do not match."),
    ])
    confirm = PasswordField("Confirm Password")

# Sign up route
@app.route("/signup/", methods=["GET", "POST"])
def signup():

    # Create an object of our registration form
    form = RegistrationForm(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.hash(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        cur.execute(
            "INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password)
        )

        # Commit to DB
        mysql.connection.commit()
        # Close connection
        cur.close()

        flash("Registration Successful. You will now be redirected to login")

        return redirect(url_for("login"))
    return render_template("signup.html", form=form)

# Login route
@app.route("/login/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Get the form fields
        username = request.form["username"]
        password_supplied = str(request.form["password"])

        # Create cursor
        cur = mysql.connection.cursor()

        # Query the database for the user
        result = cur.execute(
            "SELECT * FROM users WHERE username = %s",
            [username]
        )

        # If result is found
        if result > 0:
            # Get the hash and hold it in the password variable
            data = cur.fetchone()
            password = data["password"]

            # Compare the hash from the database with the supplied one
            if sha256_crypt.verify(password_supplied, password):
                # app.logger.info("Password Matched")
                # Passed, create a session for the user

                session["logged_in"] = True
                session["username"] = username

                flash("You are now logged in.", "success")
                return redirect(url_for("dashboard"))

            else:
                error = "Invalid username or password"
                return render_template("login.html", error=error)
            cur.close()
        else:
            error = "Username does not exist"
            return render_template("login.html", error=error)


    return render_template("login.html")

# Logout route
@app.route("/logout/")
@is_logged_in
def logout():
    session.clear()
    flash("You are now logged out", "success")
    return redirect(url_for("index"))

# Dashboard route
@app.route("/dashboard/")
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles 
    results = cur.execute("SELECT * FROM articles WHERE author = %s",
            [session["username"]]
            )

    articles = cur.fetchall()

    if results > 0:
        return render_template("dashboard.html", articles=articles)

    else:
        msg = "You currently have no written articles."
        return render_template("dashboard.html", msg=msg)

    # Close the connection
    cur.close()
    

# Defining Article Writing Form Class inheriting from the Form class imported from WTForms module
class ArticleForm(Form):
    title = StringField("Title", [validators.Length(min=4, max=200)])
    body = TextAreaField("Body", [validators.Length(min=30)])

# Write article route
@app.route("/write_article/", methods=["GET", "POST"])
@is_logged_in
def write_article():
    form = ArticleForm(request.form)

    if request.method == "POST" and form.validate():
        title = form.title.data
        body = form.body.data

        # Creat cursor object
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)", (title, body, session["username"])
        )

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash("Your article has been created.", "success")

        return redirect(url_for("dashboard"))

    return render_template("write_article.html", form=form)

# Write article route
@app.route("/edit_article/<id>/", methods=["GET", "POST"])
@is_logged_in
def edit_article(id):
    # Creat cursor
    cur = mysql.connection.cursor()

    # Get article by id
    results = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article_gotten = cur.fetchone()

    # Create the article form object
    form = ArticleForm(request.form)

    # Populate the form fields
    form.title.data = article_gotten["title"]
    form.body.data = article_gotten["body"]


    if request.method == "POST" and form.validate():

        # Get the form data posted using flask request and assign it to the variables
        title = request.form["title"]
        body = request.form["body"]

        # Creat cursor object
        cur = mysql.connection.cursor()

        # Update the database with the data passed
        cur.execute("UPDATE articles SET title = %s, body = %s WHERE id = %s", (title, body, id))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash("Your article has been updated.", "success")

        return redirect(url_for("dashboard"))

    return render_template("edit_article.html", form=form)

# Delete route
@app.route("/delete_article/<id>/", methods=["POST"])
@is_logged_in
def delete_article(id):

    # Create a cursor
    cur = mysql.connection.cursor()

    # Delete the article
    cur.execute("DELETE FROM articles WHERE id = %s", [id])

    # Commit to DB
    mysql.connection.commit()

    # Close connection
    cur.close()

    flash("Article has been deleted.", "success")

    return redirect(url_for("dashboard"))


if __name__=="__main__":
    app.secret_key = "123Abingo#-!"
    app.run(debug=True)