from app import render_template


# Set background-image based on cur["activity"]
def set_image_link(cur, ACTIVITIES):
    image_link = None
    if cur["activity"] == ACTIVITIES[0]:
        image_link = "/static/img/coding1-t.png"
    elif cur["activity"] == ACTIVITIES[1]:
        image_link = "/static/img/yoga.png"
    elif cur["activity"] == ACTIVITIES[2]:
        image_link = "/static/img/nature-t.png"
    elif cur["activity"] == ACTIVITIES[3]:
        image_link = "/static/img/mitmi-t.png"
    elif cur["activity"] == ACTIVITIES[4]:
        image_link = "/static/img/sports-t.png"
    elif cur["activity"] == ACTIVITIES[5]:
        image_link = "/static/img/noreason1-t.png"
    elif cur["activity"] == ACTIVITIES[6]:
        image_link = "/static/img/music.png"
    else:
        image_link = "/static/img/sunrise.jpg"
    return image_link


# Set background-image based on filtered
def set_image_linkv2(filtered, ACTIVITIES):
    image_link = None
    if filtered == ACTIVITIES[0]:
        image_link = "/static/img/coding1-t.png"
    elif filtered == ACTIVITIES[1]:
        image_link = "/static/img/yoga.png"
    elif filtered == ACTIVITIES[2]:
        image_link = "/static/img/nature-t.png"
    elif filtered == ACTIVITIES[3]:
        image_link = "/static/img/mitmi-t.png"
    elif filtered == ACTIVITIES[4]:
        image_link = "/static/img/sports-t.png"
    elif filtered == ACTIVITIES[5]:
        image_link = "/static/img/noreason1-t.png"
    elif filtered == ACTIVITIES[6]:
        image_link = "/static/img/music.png"
    else:
        image_link = "/static/img/sunrise.jpg"
    return image_link



# Check if all parameters are in the correct data type
def check_wimit_errors(now, today, activity, ACTIVITIES, allowed, dates, hour_1, hour_2, hour_3, place):
    if (activity not in ACTIVITIES):
        print("ERROOOOR")
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
    else:
        return
