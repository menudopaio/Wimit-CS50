from datetime import date, datetime
from functools import wraps
from cs50 import SQL
import sqlite3
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import set_image_link, check_wimit_errors, set_image_linkv2

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

# Don't update automatically each refresh
app.config['SESSION_REFRESH_EACH_REQUEST'] = False

# Don't store in cache
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///wimit.db")



# If changes here, change also layout.html
ACTIVITIES = [
    "Lets code!",
    "Yoga with Ana!",
    "In nature..",
    "Mitmi",
    "Sports",
    "No reason",
    "Play music",
    "Others"
]


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    response.headers['Vary'] = 'Cookie'
    return response


def login_required(f):
    """
    Decorate routes to require login.
    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# REGISTRATION PAGE
@app.route("/register", methods=["GET", "POST"])
def register():
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("error.html", message="Must provide a valid username")

        # Ensure password was submitted
        if not request.form.get("password") or len(request.form.get("password")) < 6:
            return render_template("error.html", message="Must enter a valid password")

        # Ensure password was confirmed
        if not request.form.get("confirmation"):
            return render_template("error.html", message="Must enter confirmation")

        # Ensure password is same in both fields
        if request.form.get("password") != request.form.get("confirmation"):
            return render_template("error.html", message="Password must match confirmation")

        # Query in database if username not in use
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if rows:
            return render_template("error.html", message="This username already exists")

        # Hash password
        hashh = generate_password_hash(request.form.get("password"))
        db.execute("INSERT INTO users(username, hash) VALUES (?, ?)", request.form.get("username"), hashh)

        # Remember which user has logged in
        user = db.execute("SELECT id FROM users WHERE username = ?", request.form.get("username"))
        session["user_id"] = user[0]["id"]

        # Redirect user to home page
        image_link = "static/img/sunrise.jpg"
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    return render_template("register.html")

# LOG IN PAGE
@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("error.html", message="Must provide a valid username")

        # Ensure password was submitted
        if not request.form.get("password"):
            return render_template("error.html", message="Must provide a valid password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("error.html", message="Invalid username or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    return render_template("login.html")

# LOG OUT ROUTE
@login_required
@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")

# HOME PAGE
@app.route("/")
def home():

    # Set today
    today = date.today()
    
    # Set image
    image_link = "static/img/sunrise.jpg"

    # Get username
    username = db.execute("SELECT * FROM users WHERE id = ?", session['user_id'])
    username = username[0]['username']

    # Select private_activities created by user
    user_private_activities = db.execute("SELECT * FROM add_wimit WHERE (allowed = 'private') AND (creator_id = ?) AND date >= ? ORDER BY date, hour_1", session["user_id"], today)

    # Select public activities created by user
    user_public_activities = db.execute("SELECT * FROM add_wimit WHERE (allowed = 'public') AND (creator_id = ?) AND date >= ? ORDER BY date, hour_1", session["user_id"], today)

    # Select private activities created by friends
    friends_private_activities = db.execute("SELECT * FROM add_wimit JOIN friends ON add_wimit.creator_id = friends.friend_id WHERE friends.user_id = ? AND date >= ? and allowed = 'private' ORDER BY date, hour_1", session["user_id"], today)
    fpa_usernames = db.execute("SELECT * FROM users JOIN friends ON users.id = friends.friend_id JOIN add_wimit ON friends.friend_id = add_wimit.creator_id WHERE friends.user_id = ? AND date >= ? ORDER BY date, hour_1", session["user_id"], today)
    
    # Select public activities not from the user
    public_activities = db.execute("SELECT * FROM add_wimit WHERE allowed = 'public' AND creator_id != ? AND n_members < max AND date >= ? ORDER BY date, hour_1", session["user_id"], today)
    pa_usernames = db.execute("SELECT * FROM users JOIN add_wimit ON users.id = add_wimit.creator_id WHERE allowed = 'public' AND creator_id != ? AND n_members < max AND date >= ? ORDER BY date, hour_1", session["user_id"], today)

    return render_template("home.html", username=username, user_private_activities=user_private_activities, user_public_activities=user_public_activities, friends_private_activities=friends_private_activities, fpa_usernames=fpa_usernames, public_activities=public_activities, pa_usernames=pa_usernames, activities=ACTIVITIES, image_link=image_link)


# MY WIM!TS PAGE
@login_required
@app.route("/mywimits")
def mywimits():
    # Set today and filter
    today = date.today()

    # Get username
    username = db.execute("SELECT * FROM users WHERE id = ?", session['user_id'])
    username = username[0]['username']
    
    # Set image and title
    image_link = "static/img/sunrise.jpg"
    title = 'My Wim!ts'

    # All activities created by session["user_id"]
    usr_act = db.execute("SELECT * FROM add_wimit WHERE creator_id = ? AND date >= ? ORDER BY date, hour_1", session['user_id'], today)
    return render_template("mywimits.html", username=username, activities=ACTIVITIES, user_activities=usr_act, image_link=image_link, title=title)


# CHECK & CHECK DETAILS ROUTES
@login_required
@app.route("/check", methods=["POST", "GET"])
def check():
    # Check wimit by its id
    if request.method == "GET":
        activity_id = request.args.get("get_id")

        # Select activity by its id
        user_wimits = db.execute("SELECT * FROM add_wimit WHERE id = ?", activity_id)
        user_wimits = user_wimits[0]
       
        # Set image based on user_wimits["activity"]
        image_link = set_image_link(user_wimits, ACTIVITIES)

        # If user is not enrolled
        usr_enrolled = db.execute("SELECT member_id FROM wimit_members WHERE wimit_id = ? AND member_id = ?", activity_id, session["user_id"])
        if (not usr_enrolled):
            return render_template("check.html", image_link=image_link, a=user_wimits, enrolled=False)
        
        # If user is enrolled
        # Get users most voted preferences
        hr1 = db.execute("SELECT * FROM wimit_members WHERE wimit_id = ? AND hour_1 = 'on'", activity_id)
        pr1 = len(hr1)
        hr2 = db.execute("SELECT * FROM wimit_members WHERE wimit_id = ? AND hour_2 = 'on'", activity_id)
        pr2 = len(hr2)
        hr3 = db.execute("SELECT * FROM wimit_members WHERE wimit_id = ? AND hour_3 = 'on'", activity_id)
        pr3 = len(hr3)

        # Set preferred hour option(s)
        hours = [pr1, pr2, pr3]
        most_voted = max(hours)
        pref = [user_wimits["hour_1"], user_wimits["hour_2"], user_wimits["hour_3"]]
        chosen = []
        hours_length = len(hours)
        for _ in range(hours_length):
            if hours[_] == most_voted:
                chosen.append(pref[_])
        
        cur_mem = db.execute("SELECT * FROM wimit_members WHERE wimit_id = ? AND member_id = ?", activity_id, session["user_id"])
        cur_mem = cur_mem[0]
        
        import matplotlib.pyplot as plt
        import numpy as np
        from io import BytesIO
        import base64

        # Datos: hours = [pr1, pr2, pr3], etiquetas = [user_wimits["hour_1"], user_wimits["hour_2"], user_wimits["hour_3"]], colores = ['green', 'cian', 'magenta']
        etiquetas = [user_wimits["hour_1"], user_wimits["hour_2"], user_wimits["hour_3"]]
        # Verde, azul, rojo
        colores = ['#00FF00', '#0090FF', '#FF4500']

        # Especifica una fuente alternativa (por ejemplo, Arial)
        plt.rcParams['font.family'] = 'Arial'

        # Tamaño fuente texto grafico
        tamano_fuente = 15

        # Crear el gráfico circular con fondo transparente
        fig, ax = plt.subplots(figsize=(3, 3))
        wedges, texts = ax.pie(hours, labels=etiquetas, colors=colores, startangle=90, textprops={'fontsize': tamano_fuente-2})

        # Agregar un círculo para formar el donut
        centro_circulo = plt.Circle((0, 0), 0.35, fc='white')
        fig.gca().add_artist(centro_circulo)


        # Ajustar la separación de las etiquetas numéricas del centro del gráfico
        separacion_factor = 1.75  # Puedes ajustar este valor según tus preferencias

        # Agregar etiquetas numéricas
        for i, (etiqueta, valor) in enumerate(zip(etiquetas, hours)):
            angle = (wedges[i].theta2 - wedges[i].theta1) / 2 + wedges[i].theta1
            x = separacion_factor * 0.35 * np.cos(angle * (3.14159 / 180))
            y = separacion_factor * 0.35 * np.sin(angle * (3.14159 / 180))
            ax.text(x, y, str(valor), ha='center', va='center', fontsize=tamano_fuente)

        # Configurar el fondo transparente
        fig.patch.set_alpha(0.0)

        # Ajustar aspecto para que se vea como un círculo
        plt.axis('equal')

        # Añadir un título
        plt.title('Chosen schedule', fontsize=tamano_fuente+1, y=1.02)

        # Convertir la imagen a formato base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', transparent=True)
        buffer.seek(0)
        imagen_base64 = base64.b64encode(buffer.read()).decode('utf-8')

        # Imprimir el código HTML con la imagen base64
        html_code = f'<img src="data:image/png;base64,{imagen_base64}" alt="Gráfico Circular">'
        
        return render_template("check_details.html", chosen=chosen, html_code=html_code, image_link=image_link, a=user_wimits, enrolled=True, hr1=pr1, hr2=pr2, hr3=pr3, cur_mem=cur_mem)

# ADD WIMIT ROUTE
@login_required
@app.route("/addwimit", methods=["POST", "GET"])
def addwimit():

    # Set today and now
    today = date.today()
    now = datetime.now()

    # Get all data from form
    if request.method == "POST":
        activity = request.form.get("activity", "Mitmi")
        allowed = request.form.get("allowed")
        mini = request.form.get("min", 1)
        maxi = request.form.get("max", 50)
        place = request.form.get("place")
        i_bring = request.form.get("i_bring", 0)
        dates = request.form.get("date")
        hour_1 = request.form.get("time_1")
        hour_2 = request.form.get("time_2")
        hour_3 = request.form.get("time_3")

        # Check if all parameters are in the correct data type
        if (activity not in ACTIVITIES):
            return render_template("error.html", message="You must select a valid activity.")
        if (not allowed):
            return render_template("error.html", message="Public or Private.")
        if (dates < today.strftime("%Y-%m-%d")):
            return render_template("error.html", message="Must provide a valid date.")
        if (not hour_1):
            return render_template("error.html", message="Must provide option Hour 1.")
        if (not hour_2 and hour_3):
            return render_template("error.html", message="First add Hour 2 option.")
        if ((hour_1 < now.strftime("%H:%M:%S")) and (dates == today.strftime("%Y-%m-%d"))):
            return render_template("error.html", message="Hour option must be later than now.")
        if ((hour_1 == hour_2) or (hour_2 == hour_3) or (hour_1 == hour_3)) and (hour_2 or hour_3):
            return render_template("error.html", message="Hour options must be different.")
        if (not place):
            return render_template("error.html", message="Must meet at some place.")
        
        # Create event in the database
        try:
            db.execute("INSERT INTO add_wimit (creator_id, activity, allowed, min, max, date, hour_1, hour_2, hour_3, i_bring, n_members, place) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)", session["user_id"], activity, allowed, mini, maxi, dates, hour_1, hour_2, hour_3, i_bring, place)
        except KeyError:
            return render_template("login.html")
        
        # Select id from current activity to store data in database
        wimit_id = db.execute("SELECT id FROM add_wimit ORDER BY id DESC LIMIT 1")
        wimit_id = wimit_id[0]
        
        # Add creator_id as new member in wimit_members
        if hour_2:
            h2on = 'on'
        else:
            h2on = None
        if hour_3:
            h3on = 'on'
        else:
            h3on = None
        db.execute("INSERT INTO wimit_members (wimit_id, member_id, date, hour_1, hour_2, hour_3) VALUES (?, ?, ?, 'on', ?, ?)", wimit_id["id"], session["user_id"], dates, h2on, h3on)
        return redirect("/")
    # GET
    # Go to add_wimit with a selected activity
    redirect_nav = request.args.get("redirect_nav")

    if (redirect_nav):
        try:
            cur = db.execute("SELECT * FROM add_wimit WHERE activity = ?", redirect_nav)
            cur = cur[0]
            image_link = set_image_link(cur, ACTIVITIES)
            return render_template("addwimit.html", activities=ACTIVITIES, image_link=image_link, today=today, now=now, redirect_nav=redirect_nav)
        except IndexError:
            return render_template("addwimit.html", activities=ACTIVITIES, image_link=image_link, today=today, now=now, redirect_nav=redirect_nav)

    image_link = "static/img/summer-t.png"
    return render_template("addwimit.html", activities=ACTIVITIES, image_link=image_link, today=today, now=now)


# JUST ENROLLED, CURRENT ROUTE
# Comming from /check["id"]->Enroll
@login_required
@app.route("/current", methods=["POST"])
def current():
    if request.method == "POST":
        # Get current activity data
        wimit_id = request.form.get("enroll_btn")
        cur = db.execute("SELECT * FROM add_wimit WHERE id = ?", wimit_id)
        cur = cur[0]

        # Get hour choices
        hour_1 = request.form.get("hour_1")
        hour_2 = request.form.get("hour_2")
        hour_3 = request.form.get("hour_3")

        # Set background-image based on cur["activity"]
        image_link = set_image_link(cur, ACTIVITIES)

        # Check if some hour option is activated
        if (hour_1 != 'on' and hour_2 != 'on' and hour_3 != 'on'):
            return render_template("error.html", message="Must enroll on at least one hour option.")
        
        # Check if user already enrolled in this activity
        it_exists = db.execute("SELECT * FROM wimit_members WHERE wimit_id = ? AND member_id = ?", wimit_id, session["user_id"])
        if (it_exists):
            return render_template("error.html", message="You are already enrolled in this activity.")

        # Update database to store preferences
        cur["n_members"] = (cur["n_members"]) + 1
        db.execute("INSERT INTO wimit_members (wimit_id, member_id, date, hour_1, hour_2, hour_3) VALUES (?, ?, ?, ?, ?, ?)", wimit_id, session["user_id"], cur["date"], hour_1, hour_2, hour_3)
        db.execute("UPDATE add_wimit SET n_members = ? WHERE id = ?", (cur["n_members"]), wimit_id)
        return render_template("current-wimits.html", cur=cur, image_link=image_link)


# Unenroll from an activity
@login_required
@app.route("/unenroll", methods=["POST"])
def unenroll():
    # Get activity id and use it to get cur["n_members"] and update it
    wimit_id = request.form.get("unenroll_btn")
    cur = db.execute("SELECT * FROM add_wimit WHERE id = ?", wimit_id)
    try:
        cur = cur[0]
    except IndexError:
        return render_template("error.html", message="Could not unenroll.")

    # Delete user from wimit_members and update n_members from add_wimit
    cur["n_members"] = (cur["n_members"]) - 1
    db.execute("DELETE FROM wimit_members WHERE wimit_id = ? AND member_id = ?", wimit_id, session["user_id"])
    db.execute("UPDATE add_wimit set n_members = ? WHERE id = ?", cur["n_members"], wimit_id)
    is_empty = db.execute("SELECT * FROM add_wimit WHERE id = ?", wimit_id)
    try:
        is_empty = is_empty[0]["n_members"]
    except IndexError:
        return render_template("error.html", message="You can not unenroll from this activity.")
    if is_empty == 0:
        db.execute("DELETE FROM add_wimit WHERE id = ?", wimit_id)
        db.execute("DELETE FROM wimit_members WHERE wimit_id = ?", wimit_id)
    return redirect("/")

# EDIT ROUTE
@login_required
@app.route("/edit", methods=["POST", "GET"])
def edit():
    # POST
    if request.method == "POST":
        # Get activity id and use it to edit options
        wimit_id = request.form.get("edit_btn")
        cur = db.execute("SELECT * FROM add_wimit WHERE id = ?", wimit_id)
        try:
            cur = cur[0]
        except IndexError:
            return render_template("error.html", message="Could not load wim!t.")
    
        image_link = set_image_link(cur, ACTIVITIES)
        return render_template("edit.html", cur=cur, image_link=image_link, activities=ACTIVITIES)
    
    return render_template("login.html")

# EDITED --> UPDATE WIMIT AND RENDER HOME PAGE
@login_required
@app.route("/edited", methods=["POST"])
def edited():
    
    # Get all data from form
    if request.method == "POST":

        # Set today and now
        today = date.today()
        now = datetime.now()

        activity = request.form.get("activity", "Mitmi")
        allowed = request.form.get("allowed")
        mini = request.form.get("min", 1)
        maxi = request.form.get("max", 50)
        place = request.form.get("place")
        i_bring = request.form.get("i_bring", 0)
        dates = request.form.get("date")
        hour_1 = request.form.get("time_1")
        hour_2 = request.form.get("time_2")
        hour_3 = request.form.get("time_3")
        id = request.form.get("change_settings")

        # ADD FUNCTION FROM helpers.py IF IT WORKS
        # Check if all parameters are in the correct data type
        if (activity not in ACTIVITIES):
            return render_template("error.html", message="Activity not allowed.")
        if (not allowed):
            return render_template("error.html", message="Public or Private.")
        if (dates < today.strftime("%Y-%m-%d")):
            return render_template("error.html", message="Must provide a valid date.")
        if (not hour_1):
            return render_template("error.html", message="Must provide option Hour 1.")
        if (not hour_2 and hour_3):
            return render_template("error.html", message="First add Hour 2 option.")
        if ((hour_1 < now.strftime("%H:%M:%S")) and (dates == today.strftime("%Y-%m-%d"))):
            return render_template("error.html", message="Hour option must be later than now.")
        if ((hour_1 == hour_2) or (hour_2 == hour_3) or (hour_1 == hour_3)) and (hour_2 or hour_3):
            return render_template("error.html", message="Hour options must be different.")
        if (not place):
            return render_template("error.html", message="Must meet at some place.")

        new_n_mem = None
        # Update wimit with new changes
        # PART OF THIS CODE CANT BE CHECKED UNTIL PRIVATE WIMITS ARE SHAREABLE BETWEEN USERS
        hours = db.execute("SELECT hour_1, hour_2, hour_3 FROM add_wimit WHERE id = ?", id)
        if hours[0]['hour_1'] != hour_1 or hours[0]['hour_2'] != hour_2 or hours[0]['hour_3'] != hour_3:
            new_n_mem = 1
            db.execute("DELETE FROM wimit_members WHERE wimit_id = ?", id)
        else:
            new_n_mem = db.execute("SELECT n_members FROM add_wimit WHERE id = ?", id)
            new_n_mem = new_n_mem[0]['n_members']

        db.execute("UPDATE add_wimit SET activity = ?, allowed = ?, min = ?, max = ?, place = ?, i_bring = ?, date = ?, hour_1 = ?, hour_2 = ?, hour_3 = ?, n_members = ? WHERE id = ?", activity, allowed, mini, maxi, place, i_bring, dates, hour_1, hour_2, hour_3, new_n_mem, id)
        if new_n_mem == 1:
            db.execute("INSERT INTO wimit_members (wimit_id, member_id, date, hour_1, hour_2, hour_3) VALUES (?, ?, ?, 'on', 'on', 'on')", id, session["user_id"], dates)
        return redirect("/")
    # GET    
        

# DELETE WIM!T ROUTE
@login_required
@app.route("/delete", methods=["POST"])
def delete():
    wimit_delete = request.form.get("delete_btn")
    db.execute("DELETE FROM add_wimit WHERE id = ?", wimit_delete)
    db.execute("DELETE FROM wimit_members WHERE wimit_id = ?", wimit_delete)
    return redirect("/")

# HOME DROPDOWN FILTERS ROUTE
@login_required
@app.route("/home-filters", methods=["GET"])
def home_filters():

    # Set today
    today = date.today()
    filtered = request.args.get("filtered")

    # Select public and private activities, filtered
    try:
        home_filtered = db.execute("SELECT * FROM add_wimit WHERE n_members < max AND date >= ? AND activity = ? ORDER BY date, hour_1", today, filtered)
            
        # Get username
        username = db.execute("SELECT * FROM users WHERE id = ?", session['user_id'])
        username = username[0]['username']

        # Select private_activities created by user
        user_private_activities = db.execute("SELECT * FROM add_wimit WHERE (allowed = 'private') AND (creator_id = ?) AND date >= ? AND activity = ? ORDER BY date, hour_1", session["user_id"], today, filtered)

        # Select public activities created by user
        user_public_activities = db.execute("SELECT * FROM add_wimit WHERE (allowed = 'public') AND (creator_id = ?) AND date >= ? AND activity = ? ORDER BY date, hour_1", session["user_id"], today, filtered)

        # Select private activities created by friends
        friends_private_activities = db.execute("SELECT * FROM add_wimit JOIN friends ON add_wimit.creator_id = friends.friend_id WHERE friends.user_id = ? AND date >= ? AND activity = ? ORDER BY date, hour_1", session["user_id"], today, filtered)
        fpa_usernames = db.execute("SELECT * FROM users JOIN friends ON users.id = friends.friend_id JOIN add_wimit ON friends.friend_id = add_wimit.creator_id WHERE friends.user_id = ? AND date >= ? AND activity = ? ORDER BY date, hour_1", session["user_id"], today, filtered)
        
        # Select public activities 
        public_activities = db.execute("SELECT * FROM add_wimit WHERE (allowed = 'public') AND creator_id != ? AND (n_members < max) AND date >= ? AND activity = ? ORDER BY date, hour_1", session["user_id"], today, filtered)
        pa_usernames = db.execute("SELECT * FROM users JOIN add_wimit ON users.id = add_wimit.creator_id WHERE allowed = 'public' AND creator_id != ? AND n_members < max AND date >= ? AND activity = ? ORDER BY date, hour_1", session["user_id"], today, filtered)

        
        # If filter selected
        if (home_filtered):
            image_link = set_image_link(home_filtered[0], ACTIVITIES)
            return render_template("home.html", activities=ACTIVITIES, user_public_activities=user_public_activities, user_private_activities=user_private_activities, friends_private_activities=friends_private_activities, fpa_usernames=fpa_usernames, public_activities=public_activities, pa_usernames=pa_usernames, image_link=image_link, title='My Wim!ts - ' + filtered)

        # If filter = All
        if (filtered == 'all'):
            usr_act = db.execute("SELECT * FROM add_wimit WHERE n_members < max AND date >= ?", session["user_id"], today)
            image_link = "static/img/sunrise.jpg"
            return render_template("home.html", activities=ACTIVITIES, user_activities=usr_act, image_link=image_link, title='My Wim!ts - All')
        else:
            image_link = set_image_link(home_filtered[0], ACTIVITIES)
            return render_template("home.html", username=username, user_private_activities=user_private_activities, user_public_activities=user_public_activities, friends_private_activities=friends_private_activities, fpa_usernames=fpa_usernames, public_activities=public_activities, pa_usernames=pa_usernames, activities=ACTIVITIES, image_link=image_link)

    except (KeyError, IndexError):
        image_link = set_image_linkv2(filtered, ACTIVITIES)
        return render_template("home.html", activities=ACTIVITIES, image_link=image_link)



# MY WIM!TS DROPDOWN FILTERS ROUTE
@login_required
@app.route("/mywimits-filters", methods=["GET"])
def mywimits_filters():

    # Set today
    today = date.today()
    filtered = request.args.get("filtered")

    # Get username
    username = db.execute("SELECT * FROM users WHERE id = ?", session['user_id'])
    username = username[0]['username']
    
    if filtered is None:
        # Set image and title
        image_link = "static/img/sunrise.jpg"
        title = 'My Wim!ts2'
        print("DOS")
        # All activities created by session["user_id"]
        usr_act = db.execute("SELECT * FROM add_wimit WHERE creator_id = ? AND date >= ? ORDER BY date, hour_1", session['user_id'], today)
        return render_template("mywimits.html", username=username, activities=ACTIVITIES, user_activities=usr_act, image_link=image_link, title=title)
    
    elif (filtered == 'all'):
        usr_act = db.execute("SELECT * FROM add_wimit WHERE creator_id = ? AND date >= ?", session["user_id"], today)
        image_link = "static/img/sunrise.jpg"
        return render_template("mywimits.html", username=username, activities=ACTIVITIES, user_activities=usr_act, image_link=image_link, title='My Wim!ts - All')

    else:
        # Ejecutar la consulta
        my_filtered = db.execute("SELECT * FROM add_wimit WHERE creator_id = ? AND date >= ? AND activity = ? ORDER BY date, hour_1", session['user_id'], today, filtered) 
        title = 'My Wim!ts - ' + filtered
        try:
            image_link = set_image_link(my_filtered[0], ACTIVITIES)
        except IndexError:
            image_link = set_image_linkv2(filtered, ACTIVITIES)
        return render_template("mywimits.html", image_link=image_link, activities=ACTIVITIES, username=username, user_activities=my_filtered, title=title)


@login_required
@app.route("/friends", methods=["GET"])
def friends():
    # GET
    image_link = "static/img/friendshiphot.jpg"
    
    # Check if user has friend requests and/or friends
    friends = db.execute("SELECT friend_request.id, user1_id, username, status, friends_since FROM friend_request JOIN users ON friend_request.user1_id = users.id WHERE friend_request.user2_id = ?", session['user_id'])
    friends2 = db.execute("SELECT user2_id, username, status, friends_since FROM friend_request JOIN users ON friend_request.user2_id = users.id WHERE friend_request.user1_id = ?", session['user_id'])
    if friends and friends2:
        return render_template("friends.html", friends=friends, friends2=friends2, image_link=image_link)
    elif friends:
        return render_template("friends.html", friends=friends, image_link=image_link)
    elif friends2:
        return render_template("friends.html", friends2=friends2, image_link=image_link)
    else:
        return render_template("friends.html", image_link=image_link)


# ADD NEW FRIEND (NO SUCCESS MESSAGE)
@login_required
@app.route("/search-friend", methods=["POST"])
def search_friends():
    # POST
    if request.method == "POST":
        friend_username = request.form.get("friends")
        try:
            friend_data = db.execute("SELECT id, username FROM users WHERE username = ?", friend_username)

            # Check if user tries to find himself
            if friend_data[0]['id'] == session['user_id']:
                return render_template("error.html", message="You should already be your friend!")
        except IndexError:
            return render_template("error.html", message="Could not find username.")

        # Access data from session["user_id"]
        usr_data = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
        usr_data = usr_data[0]

        # Check if user already had sent a friend request. If not, insert into database
        if (db.execute("SELECT * FROM friend_request WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)", session["user_id"], friend_data[0]['id'], friend_data[0]['id'], session["user_id"])):
            return render_template("error.html", message="You cannot send another friend request to that user.")
        else:
            db.execute("INSERT INTO friend_request (user1_id, user2_id, status) VALUES (?, ?, 'Pending')", session['user_id'], friend_data[0]['id'])
            
        # Get all friend requests from session["user_id"]
        try:
            image_link = "static/img/sunrise.jpg"
            # Check if user has friend requests and/or friends
            friends = db.execute("SELECT friend_request.id, user1_id, username, status, friends_since FROM friend_request JOIN users ON friend_request.user1_id = users.id WHERE friend_request.user2_id = ?", session['user_id'])
            friends2 = db.execute("SELECT user2_id, username, status, friends_since FROM friend_request JOIN users ON friend_request.user2_id = users.id WHERE friend_request.user1_id = ?", session['user_id'])
            if friends and friends2:
                return render_template("friends.html", friends=friends, friends2=friends2, image_link=image_link)
            elif friends:
                return render_template("friends.html", friends=friends, image_link=image_link)
            elif friends2:
                return render_template("friends.html", friends2=friends2, image_link=image_link)
            else:
                return render_template("friends.html", image_link=image_link)
            
        except IndexError:
            return redirect("/")


@login_required
@app.route("/accept-reject", methods=["POST"])
def accept_reject():
    id_a = request.form.get("accept_friend")
    if id_a:
        db.execute("UPDATE friend_request SET status = 'Accepted' WHERE id = ?", id_a)
        
        friends = db.execute("SELECT user1_id, user2_id FROM friend_request WHERE id = ?", id_a)
        friends = friends[0]
        print(friends['user1_id'])
        print(friends['user2_id'])
        db.execute("INSERT INTO friends (user_id, friend_id) VALUES (?, ?)",  friends['user1_id'], friends['user2_id'])
        db.execute("INSERT INTO friends (user_id, friend_id) VALUES (?, ?)", friends['user2_id'], friends['user1_id'])
    else:
        id_r = request.form.get("reject_friend")
        db.execute("UPDATE friend_request SET status = 'Rejected' WHERE id = ?", id_r)

    return redirect("/friends")
