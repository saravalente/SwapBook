# hellooooo guys waddup
#  Final Project
#
#  application.py
#
#  William S Baughman, Elizabeth Healey, Sara Valente
#  wbaughman@college.harvard.edu, ehealey@college.harvard.edu, saravalente@college.harvard.edu
# 
#  Implements a textbook resale website
#

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import gettempdir

from helpers import *
#da fuq?

import string

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response


# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = gettempdir()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///tables.db")

@app.route("/home", methods=["GET"])
def home():
    
    return render_template("home.html")

@app.route("/", methods=["GET", "POST"])
@login_required
def index():

    # get five most recent textbook listings
    rows = db.execute("SELECT * FROM textbooks WHERE status = :status ORDER BY listingid DESC LIMIT 5", status='listed')
    
    # get first part of user's username for welcome message
    name = db.execute("SELECT username FROM users WHERE id = :identity", identity=session["user_id"])
    fullname = name[0]["username"]
    username = fullname.split(' ', 1)[0]
    
    # render the template with the textbook feed and user greeting appropriately passed
    return render_template("index.html", displays=rows, name=username)
    


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    
    
    # if form submitted
    if request.method == "POST":
        
        # select all listed textbooks whose names anywhere contain the input value
        q = request.form.get("class")
        lists = db.execute("SELECT * FROM textbooks WHERE course LIKE :course AND status = :status ORDER BY price", course='%' + q + '%', status='listed')
        
        # if a button was pressed to comment, get the username of the seller and the id of the textbook
        if 'name' in request.form:
            listingid = request.form['name']
            rows = db.execute("SELECT * FROM textbooks WHERE listingid = :listingid",  listingid=listingid)
            username = rows[0]['posterusrnm']
            
            # direct user to a page to send comment
            return render_template("comment.html", username=username, listingid=listingid)
            
        # create a checking variable to determine if any results were gotten
        nosearchresults = 1
        if not lists:
            nosearchresults = 0
            
        # update the buy.html with results if any were found, other if results not found
        return render_template("buy.html", lists=lists, nosearchresults=nosearchresults)
    
    # render buy.html upon GET    
    else:
        return render_template("buy.html")

    
@app.route("/mylistings", methods=["GET", "POST"])
@login_required
def mylistings():
    
    # if POST method
    if request.method == "POST":
        
        # if button to change listing status is clicked, store in variable "book" the listingid of that book
        book = request.form['name']
        
        # query the textbooks SQL table for the current status of the book whose status is to be changed
        rows = db.execute("SELECT status FROM textbooks WHERE posterid = :identity AND listingid = :listingid", identity=session["user_id"], listingid=book)
        
        # store this value in the variable "status"
        status = rows[0]['status']
        
        # change status of this book from listed to unlisted, or vice versa
        if status == 'listed':
            db.execute("UPDATE textbooks SET status = :status WHERE posterid = :identity AND listingid = :listingid", status='unlisted', identity=session["user_id"], listingid=book)
        if status == 'unlisted':
            db.execute("UPDATE textbooks SET status = :status WHERE posterid = :identity AND listingid = :listingid", status='listed', identity=session["user_id"], listingid=book)
        
        # refresh the page with new listing status
        return redirect(url_for("mylistings"))
    
    # if GET method
    else:
        
        # select all of the textbooks listed by this user ordered by most recently posted
        rows = db.execute("SELECT * FROM textbooks WHERE posterid = :identity ORDER BY listingid DESC", identity=session["user_id"])
    
        # render the template that will display these listings
        return render_template("mylistings.html", textbooks=rows)
    

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        # initialize a validity variable (will be used to provide error message)
        invalid = 0
        
        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=string.capwords(request.form.get("username")))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            
            # activate the validity variable and reload login.html so it will contain error message
            invalid = 1
            return render_template("login.html", invalid=invalid)

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        
        # just return the virgin template
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # get name
    rows = db.execute("SELECT username FROM users WHERE id = :identity", identity=session["user_id"])
    name = rows[0]["username"]
    byename = string.capwords(name.split(' ', 1)[0])
    
    # forget any user_id
    session.clear()

    # redirect user to login form
    return render_template("goodbye.html", name=byename)
    
@app.route("/about", methods=["GET"])
def about():
    """About the website."""
    
    # render the static "about" template
    return render_template("about.html")
    

@app.route("/register", methods=["GET", "POST"])
def register():
    
    # if reached via POST
    if request.method == "POST":
        
        # initialize some variables to determine which errors to display
        userused = 0
        emailused = 0
        collegeused = 0
        
        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
        
        # if username is already in use, display error
        if len(rows) != 0:
            userused = 1
            return render_template("register.html", userused=userused)
        
        # query databse for email
        emailaddress = db.execute("SELECT * FROM users WHERE email = :email", email=request.form.get("email"))
        
        # if email is already is use, display error
        if len(emailaddress) != 0:
            emailused = 1
            return render_template("register.html", emailused=emailused)
        
        # get email
        email = request.form.get("email")
        
        # require that user uses harvard email 
        if "@college.harvard.edu" not in email:
            collegeused = 1
            return render_template("register.html", collegeused=collegeused)
        
        
        # register user in SQL table
        db.execute("INSERT INTO users (username, hash, house, email, year) VALUES(:username, :password, :house, :email, :year)", 
            username=string.capwords(request.form["username"]), password=pwd_context.encrypt(request.form["password"]), house=string.capwords(request.form["house"]), 
            email=request.form["email"], year=request.form["year"])
        
        # log user in
        return redirect(url_for("login"))
    
    # return template on default    
    else:
        
        return render_template("register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    
    # if form submitted
    if request.method == "POST":
        
        # get all the identifying information of the new seller
        emailaddressrows = db.execute("SELECT email FROM users WHERE id = :identity", identity=session["user_id"])
        emailaddress = emailaddressrows[0]["email"]
        
        usernamerows = db.execute("SELECT username FROM users WHERE id = :identity", identity=session["user_id"])
        username = usernamerows[0]["username"]
        
        yearrows = db.execute("SELECT year FROM users WHERE id = :identity", identity=session["user_id"])
        year = yearrows[0]["year"]
        
        houserows = db.execute("SELECT house FROM users WHERE id = :identity", identity=session["user_id"])
        house = houserows[0]["house"]

        # insert into the textbooks table all the information of the new textbook to be listed as for sale
        db.execute("INSERT INTO textbooks (course, textbook, price, notes, posterid, posterusrnm, year, email, house, status) VALUES(:course, :textbook, :price, :notes, :posterid, :username, :year, :email, :house, :status)", 
        course=request.form["course"], textbook=request.form["textbook"], 
        price=request.form["price"], notes=request.form["notes"], posterid=session["user_id"],
        username=username, year=year, email=emailaddress, house=house, status='listed')
        
        # return user to index
        return redirect(url_for("index"))
    
    # render template on default    
    else:
        
        return render_template("sell.html")
        
@app.route("/comment", methods=["GET", "POST"])
@login_required
def comment():
    
    # if form submitted
    if request.method == "POST":
        message = request.form["message"]
        listingid = request.form["sendbutton"]
        
        # get info about textbook
        rows = db.execute("SELECT * FROM textbooks WHERE listingid = :listingid",  listingid=listingid)
        receiverusername = rows[0]['posterusrnm']
        receiverid = rows[0]['posterid']
        textbook = rows[0]['textbook']
        
        # get info about user
        nextrows = db.execute("SELECT * FROM users WHERE id = :identity",  identity=session["user_id"])
        senderusername = nextrows[0]['username']
        senderid = nextrows[0]['id']
        
        # make sure this conversation doesnt alreay exit
        if not db.execute("Select * FROM conversations WHERE buyerid = :buyerid AND listingid = :listingid", buyerid=senderid, listingid=listingid):
            db.execute("INSERT INTO conversations (sellerid, buyerid, listingid, textbook, buyerusername, sellersusername) VALUES(:sellerid, :buyerid, :listingid, :textbook, :buyerusername, :sellerusername)", 
            sellerid = receiverid, buyerid=senderid, listingid=listingid,  textbook=textbook, buyerusername = senderusername, sellerusername = receiverusername)
        
        #get the convo id
        convoidfind = db.execute("Select * FROM conversations WHERE buyerid = :buyerid AND listingid = :listingid", buyerid=senderid, listingid=listingid)
        convoid = convoidfind[0]['convoid']
        print(convoid)
        db.execute("INSERT INTO comments (comment, textbook, listingid, senderid, receiverid, senderusername, convoid) VALUES(:comment, :textbook, :listingid, :senderid, :receiverid, :senderusername, :convoid)", 
        comment = message, textbook=textbook, listingid=listingid, senderid=senderid, receiverid=receiverid, senderusername=senderusername, convoid=convoid)

        # return user to buy
        returnlist = db.execute("SELECT * FROM textbooks WHERE listingid = :listingid", listingid=listingid)
        return render_template("buy.html", lists=returnlist)
    
    # render template on default    
    else:
        return render_template("comment.html")
        
@app.route("/inbox", methods=["GET", "POST"])
@login_required
def inbox():
    
    # if form submitted
    if request.method == "POST":
    
        
        #get info about the convo
        convoid = request.form['click']
        
        # get info about conversation
        therows = db.execute("SELECT * FROM conversations WHERE convoid = :identity",  identity= convoid)
        listingid = therows[0]['listingid']
        person1 = therows[0]['sellerid']
        person2 = therows[0]['buyerid']
        
        rows = db.execute("SELECT * FROM comments WHERE  (convoid = :convoid)",  convoid=convoid)


        #get info about textbook
        textbooks = db.execute("SELECT * FROM textbooks WHERE listingid = :identity",  identity= listingid)

        #figure out if youre a buyer or seller
        youare =session["user_id"]
        if float(youare) == float(person1):
            profile = db.execute("SELECT * FROM users WHERE id = :identity",  identity= person2)
        else:
            profile = db.execute("SELECT * FROM users WHERE id = :identity",  identity= person1)
        
        # return user to index
        return render_template("conversation.html", rows=rows, profile=profile, textbooks= textbooks, convoid=convoid)
    # render template on default    
    else:
        
        # get all comments where user is involved
        buying = db.execute("SELECT * FROM conversations WHERE buyerid = :identity",  identity=session["user_id"])
        selling = db.execute("SELECT * FROM conversations WHERE sellerid = :identity",  identity=session["user_id"])
     
        
        return render_template("inbox.html", buying=buying, selling=selling)
        
@app.route("/conversation", methods=["GET", "POST"])
@login_required
def conversation():
    
    # if form submitted
    if request.method == "POST":
        # get info from webpage
        convoid = request.form["sendbutton"]
        message = request.form["message"]

        
        therows = db.execute("SELECT * FROM conversations WHERE convoid = :identity",  identity = convoid)
        #collect info about conversation 
        listingid = therows[0]['listingid']
        sellerid = therows[0]['sellerid']
        buyerid = therows[0]['buyerid']

        #get info about textbook
        textbooks = db.execute("SELECT * FROM textbooks WHERE listingid = :identity",  identity= listingid)
        
        youare =session["user_id"]
        # get info of person you are communicating with
        if float(youare) == float(sellerid):
            profile = db.execute("SELECT * FROM users WHERE id = :identity",  identity= buyerid)
        else:
            profile = db.execute("SELECT * FROM users WHERE id = :identity",  identity= sellerid)
        
        # get info about seller of textbook
        initialseller = textbooks[0]['posterusrnm']
        initialsellerid = textbooks[0]['posterid']
        textbook = textbooks[0]['textbook']
        
        # gets your info as the sender
        yourinfo = db.execute("SELECT * FROM users WHERE id = :identity",  identity=session["user_id"])
        senderusername = yourinfo[0]['username']
        senderid = yourinfo[0]['id']
        
        #send message to person who is not you
        if float(senderid) == float(sellerid):
            newreceiver = buyerid
        else:
            newreceiver = sellerid
        db.execute("INSERT INTO comments (comment, textbook, listingid, senderid, receiverid, senderusername, convoid) VALUES(:comment, :textbook, :listingid, :senderid, :receiverid, :senderusername, :convoid)", 
            comment = message, textbook=textbook, listingid=listingid, senderid=senderid, receiverid=newreceiver, senderusername=senderusername, convoid=convoid)
        rows = db.execute("SELECT * FROM comments WHERE  (convoid = :convoid)",  convoid=convoid)
        # return user to index
        #return render_template("conversation.html", rows=rows, profile=profile, textbooks= textbooks, convoid=convoid)
        return redirect(url_for("messagesubmitted"))

    
    # render template on default    
    else:
        
        # get all comments where user is involved
        buying = db.execute("SELECT * FROM conversations WHERE buyerid = :identity",  identity=session["user_id"])
        selling = db.execute("SELECT * FROM conversations WHERE sellerid = :identity",  identity=session["user_id"])

        return render_template("inbox.html", buying=buying, selling=selling)
        
@app.route("/messagesubmitted", methods=["GET"])
def messagesubmitted():
    """Message Submitted"""
    
    # render the static "about" template
    return render_template("messagesubmitted.html")
    