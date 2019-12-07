from flask import Flask, current_app, render_template, request, session, flash, redirect, url_for

# Importing custom classes
from classes.store_database import StoreDatabase
from classes.sell_item import SellItem
from classes.lostfound_database import LFPost, LFDatabase
from classes.user_database import User, UserDatabase

import dbinit

import psycopg2 as dbapi2
from hashlib import sha256  # hashing passwords

import random  # for tests


connection_string = "dbname='postgres' user='postgres' password='postgrepass' host='localhost' port=5432"

app = Flask(__name__)
app.secret_key = b'dsfghj+*/-8lo98k'


store_db = StoreDatabase()
lf_db = LFDatabase()
user_db = UserDatabase()


app.config["STORE_DB"] = store_db
app.config["LF_DB"] = lf_db
app.config["USER_DB"] = user_db

# 
# HOME PAGE VIEW FUNCTION 
#
@app.route("/")
def home_page():
    return render_template("index.html")


# 
# LOST ITEM PAGES VIEW FUNCTIONS 
#
@app.route("/lostfound", methods=["POST", "GET"])
def lostfound_page():
    lf_db = current_app.config["LF_DB"]
    posts = lf_db.get_all_posts()

    if request.method == "POST":
        if not session.get("is_loggedin", False):   # if not logged in, log in :)
            flash("You must login first to do that!", "error")
            return redirect("/login")

        title = request.form.get("title")
        description = request.form.get("description")
        userid = random.randint(1, 3)
        LF = request.form.get("LF")
        location = request.form.get("location")

        if title == "" or description == "" or LF == None:
            return render_template("lost_and_found.html", posts=posts)
        else:
            lfpost = LFPost(title, description, userid, LF, location=location)
            lf_db.add_post(lfpost)
            posts = lf_db.get_all_posts()
            current_app.config["LF_DB"] = lf_db

    return render_template("lost_and_found.html", posts=posts)


@app.route("/lostfound/<int:postid>", methods=["POST", "GET"])
def lfpost_page(postid):
    lf_db = current_app.config["LF_DB"]
    post, extra = lf_db.get_post(postid)
    responses = None
    return render_template("lfpost.html", post=post, extra=extra, responses=responses)



# 
# STORE PAGES VIEW FUNCTIONS 
#
@app.route("/store", endpoint='store_page', methods=["POST", "GET"])
def store_page():
    store_db = current_app.config["STORE_DB"]
    user_db = current_app.config["USER_DB"]

    if request.method == "POST":
        if request.form.get("form_key") == "sell":
            # sell form submitted
            if not ("is_loggedin" in session) or (not session["is_loggedin"]):
                # not logged in -> cannot sell item
                # redirect to login
                return redirect(url_for('login_page'))

            item_name = request.form.get("item_name")
            price = request.form.get("price")
            seller_name = session["username"]
            shortD = request.form.get("shortD")  # handle empty case!
            image = request.form.get("image")  # handle empty case!

            sellItem = SellItem(-1, item_name, price, seller_name, 0, 0, shortD, image)
            store_db.add_selling_item(sellItem)
            selling_items = store_db.get_all_selling_items()
            selling_items = sorted(selling_items)
            filter_items = [('', '', '', '')]
            return render_template("store.html", selling_items=selling_items, filter_items=filter_items)

        elif request.form.get("form_key") == "login":
            # login form submitted
            return redirect(url_for('login_page'))

        elif request.form.get("form_key") == "filter":
            # filter form submitted
            item_name = request.form.get("item_name")
            price_lw = request.form.get("price_lw")
            price_hi = request.form.get("price_hi")
            seller_name = request.form.get("seller_name")

            if request.form.get("drop_filter"):
                selling_items = store_db.get_all_selling_items()
                filter_items = [('', '', '', '')]
            else:
                selling_items = store_db.get_all_selling_items(item_name=item_name, seller_name=seller_name, price_lw=price_lw, price_hi=price_hi)
                filter_items = [(item_name, seller_name, price_lw, price_hi)]

            selling_items = sorted(selling_items)

            return render_template("store.html", selling_items=selling_items, filter_items=filter_items)

    selling_items = store_db.get_all_selling_items()
    selling_items = sorted(selling_items)
    filter_items = [('', '', '', '')]
    return render_template("store.html", selling_items=selling_items, filter_items=filter_items)


@app.route("/store/<int:sellid>", methods=["POST", "GET"])
def storePost_page(sellid):
    post = {'sellid': sellid}

    return render_template("storePost.html", post=post)


# 
# LOGIN - LOGOUT - REGISTER FUNCTIONS 
#
@app.route("/register", methods=["POST", "GET"])
def register_page():
    user_db = current_app.config["USER_DB"]

    if request.method == "POST":
        user_name = request.form.get("username")
        user_department = request.form.get("department")
        user_studentno = request.form.get("studentno")
        user_grade = request.form.get("grade")
        user_password = request.form.get("password1")
        password_check = request.form.get("password2")

        if(password_check != user_password):
            # passwords dont match
            return redirect(url_for('register_page'))

        user_password_hash = sha256(user_password.encode()).hexdigest()
        user = User(user_name, user_department, user_studentno, user_grade, user_password_hash)

        user_db.register_user(user)

        return redirect(url_for('home_page'))

    return render_template("register.html")


@app.route("/login", methods=["POST", "GET"])
def login_page():
    if session.get("is_loggedin", False):
        flash("You are already logged in as {}.".format(session.get("username")), "warning")
        return redirect("/")

    print("\n\n\n", session, "\n\n\n")    # DEBUG
    user_db = current_app.config["USER_DB"]

    if request.method == "POST":
        username = request.form.get("username")
        user = user_db.get_user_by_username(username)
        if user == None:
            print("NO USER")
            flash("Invalid username. Are you registered?", "error")
            return redirect("/login")

        password = request.form.get("password")

        hashed_password = sha256(password.encode()).hexdigest()
        print("\n\n\n", password, hashed_password, user.password_hash, "\n\n\n")

        if hashed_password != user.password_hash:
            print("WRONG PASS")
            flash("Incorrect password. Try again or Register.", "error")
            return redirect("/login")

        flash("Successfully logged in as {}".format(username), "info")
        session["username"] = username
        session["is_loggedin"] = True

        return redirect("/")

    return render_template("login.html")


@app.route("/logout", methods=["POST", "GET"])
def logout_page():
    session.clear()
    flash("Successfully logged out.", "info")
    return redirect(url_for('home_page'))


if __name__ == "__main__":
    # dbinit.initialize(connection_string)
    # app = create_app(app)
    app.run(debug=True)
