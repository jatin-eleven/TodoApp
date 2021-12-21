# Creating Env = virtualenv env 
# Activate env = .\env\Scripts\activate.ps1

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from pytz import timezone 
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask_login import LoginManager
from os import path
import requests
from authlib.integrations.flask_client import OAuth


app = Flask(__name__)
DB_NAME = "database.db"
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_NAME}"


app.config['SECRET_KEY'] = 'super secret key'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# # # ------------------------------------
oauth = OAuth(app)

app.config['SECRET_KEY'] = "THIS SHOULD BE SECRET"
app.config['GOOGLE_CLIENT_ID'] = "731593533571-n0to7imjmop87i1t69tv6ogiu7d0qrkf.apps.googleusercontent.com"
app.config['GOOGLE_CLIENT_SECRET'] = "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"

google = oauth.register(
    name = 'google',
    client_id = app.config["GOOGLE_CLIENT_ID"],
    client_secret = app.config["GOOGLE_CLIENT_SECRET"],
    access_token_url = 'https://accounts.google.com/o/oauth2/token',
    access_token_params = None,
    authorize_url = 'https://accounts.google.com/o/oauth2/auth',
    authorize_params = None,
    api_base_url = 'https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint = 'https://openidconnect.googleapis.com/v1/userinfo',  # This is only needed if using openId to fetch user info
    client_kwargs = {'scope': 'openid email profile'},
)
# # # ------------------------------------



def create_database(app):
    if not path.exists("./" + DB_NAME):
        db.create_all(app=app)
        print(" >> DataBase Created !")

create_database(app)


login_manager = LoginManager()
# when user is not logged in it redirects to the login page...
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


# # defining classes...
class Todo(db.Model):
    # sno = db.Column(db.Integer)
    id = db.Column(db.Integer, primary_key=True)
    # it should not be null...
    title = db.Column(db.String(200))
    desc = db.Column(db.String(600))
    date_time = datetime.now(timezone("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S.%f')
    date_created = db.Column(db.String(20))
    # user_id = db.Column(db.Integer, db.ForeignKey("user.sno"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __repr__(self) -> str:
        return f"{self.id} - {self.title} - {self.user_id}"


class User(db.Model, UserMixin):
    # Defining Schema for the datbase.....
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150)) 
    picture = db.Column(db.String(100))
    first_name = db.Column(db.String(150)) 
    todos =  db.relationship("Todo")  # using capital N here

    def __repr__(self) -> str:
        return f"{self.id} - {self.email} - {self.picture}"



@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    if request.method == "POST":
        title = request.form['title']
        desc = request.form['desc']
        date_time = datetime.now(timezone("Asia/Kolkata")).strftime('%d %b %Y - %H:%M')
        users = User.query.all()
        # print(" >> users : ", users)
        # print(" >> users len : ", len(users))
        
        if len(title) > 0:
            todo = Todo(title=title, desc=desc, date_created=date_time, user_id=current_user.id)
            db.session.add(todo)
            db.session.commit()
            flash("Note Added!", category="success")
    
    print(" >> Current user : ", current_user)
    # print(" >> Current user id : ", current_user.id)

    return render_template("index.html", user=current_user)


# # # ------------------------------------------
# Google login route
@app.route('/login/google')
def google_login():
    google = oauth.create_client('google')
    redirect_uri = url_for('google_authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

# Google authorize route
@app.route('/login/google/authorize')
def google_authorize():
    google = oauth.create_client('google')
    token = google.authorize_access_token()
    resp = google.get('userinfo').json()
    print(f"\n >> {resp}\n")
    print(" >> email : ", resp["email"])
    print("You are successfully signed in using google. enjoy my boy")

    email = resp["email"]
    first_name = resp["name"]
    picture = resp["picture"]

    userchk = User.query.filter_by(email=email).first()
    # note = Todo.query.get(3)
    # print("\tNote : ", note)
    if userchk:
        print("\t >> USER EXISTS")
        user = User.query.filter_by(email=email).first()
        login_user(user, remember=True) 
    else:
        new_user = User(email=email, first_name=first_name, picture=picture)
        db.session.add(new_user)
        db.session.commit()
        user = User.query.filter_by(email=email).first()
        login_user(user, remember=True)
        flash("Account Created!", category="success")

    return redirect(url_for("home"))

"""
This is we get when user is logged in by google auth...
{
    'id': '116477303547321764339',
    'email': 'jimmysharma00000m@gmail.com', 
    'verified_email': True, 
    'name': 'JATIN SUTHAR', 
    'given_name': 'JATIN', 
    'family_name': 'SUTHAR', 
    'picture': 'https://lh3.googleusercontent.com/a-/AOh14Ghu1tjxMZj_-_2K6zjR4G2gZMW0Ytta3auw_GWj9w=s96-c', 
    'locale': 'en'
}
"""
# # # ------------------------------------------


@app.route("/update/<int:id>", methods=["GET", "POST"])
def update(id):
    if request.method == "POST":
        title = request.form['title']
        desc = request.form['desc']
        date_time = datetime.now(timezone("Asia/Kolkata")).strftime('%d %b %Y - %H:%M')
        todo = Todo.query.filter_by(id=id).first()
        todo.title = title
        todo.desc = desc
        todo.date_created = date_time
        db.session.add(todo)
        db.session.commit()
        flash("Todo Updated!", category="success")
        return redirect("/")

    todo = Todo.query.filter_by(id=id).first()
    return render_template("update.html", user=current_user, todo=todo)


# # taking sno from the url as an integer and passing to the below function
@app.route("/delete/<int:id>")
def delete(id):
    # # filter the records by sno and taking the first record from it...
    todo = Todo.query.filter_by(id=id).first()
    # # deleting that record
    db.session.delete(todo)
    db.session.commit()
    flash("Todo Deleted!", category="success")
    # # after deleting it redirects us to the home page...
    return redirect("/")
    # return jsonify({})


# @app.route("/delete", methods=["POST"])
# def delete_note():
#     note = json.loads(request.data)
#     noteId = note["noteId"]
#     # getting the primary key...
#     note = Todo.query.get(noteId) 
#     if note:
#         if note.user_id == current_user.id:
#             db.session.delete(note)
#             db.session.commit()
#     # return jsonify({})
#     return redirect("/")


@app.route("/delete_acc_data/<int:id>")
def delete_acc_data(id):
    todo = Todo.query.filter_by(user_id=id).all()
    print("todo : ", todo)
    if todo:
        for i in todo:
            db.session.delete(i)
            db.session.commit()
        flash("All Todo's Deleted!", category="success")
    else:
        flash("Nothing to delete", category="error")
    return redirect("/")


@app.route("/delete_acc/<int:id>")
def delete_acc(id):
    todo = Todo.query.filter_by(user_id=id).all()
    if todo:
        for i in todo:
            db.session.delete(i)
            db.session.commit()
    else:
        pass 
    usr = User.query.filter_by(id=id).first()
    db.session.delete(usr)
    db.session.commit()

    flash("Account Deleted!", category="success")
    return redirect("/sign-up")



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        # filter the list by email and gives the only first field 
        # (here it should have only one field...)
        user = User.query.filter_by(email=email).first()
        print("USER : ", user)
        if user:
            if check_password_hash(user.password, password):
                flash("Logged in successfully!", category="success")
                # remembers the logged in user untill the browser history is cleared or server in closed.
                login_user(user, remember=True)
                return redirect(url_for("home"))
            else:
                flash("Incorrect password, try again.", category="error")
        else:
            flash("Email does not exist.", category="error")
    # print(">>>>>>>>>>>>>>>>>>>>>>> Current User : ",current_user.id)
    return render_template("login.html", user=current_user)


@app.route("/logout")
@login_required  # decorator
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/sign-up", methods=["GET", "POST"])
def sign_up():
    if request.method == "POST":
        email = request.form.get("email")
        first_name = request.form.get("firstName")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")
        
        user = User.query.filter_by(email=email).first()
        print("USERS : ", user)
        if user:
            flash("Email already exists.", category="error")
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
            # flash("Email must be greater than 3 characters.", category="error")
        elif len(first_name) < 2:
            flash("First name must be greater than 1 characters.", category="error")
        elif password1 != password2:
            flash("Passwords don't match.", category="error")
        elif len(password1) < 7:
            flash("Passwords must be at least 7 characters.", category="error")
        else:
            new_user = User(email=email, first_name=first_name, password=generate_password_hash(password1, method="sha256"))
            # it will convert password into Hash by using "sha256" algo.....
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)

            flash("Account Created!", category="success")

            return redirect(url_for("home"))

    return render_template("sign_up.html", user=current_user)



if __name__ == "__main__":
    app.run(debug=True, port=5000)
