from flask import Flask, request, jsonify, session
import pymysql
from flaskext.mysql import MySQL
from datetime import datetime

app = Flask(__name__)
app.config.update(
    DEBUG=True,
    SECRET_KEY="secret_sauce",
    SESSION_COOKIE_HTTPONLY=True,
    REMEMBER_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Strict"
)

# connect
mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'root'
app.config['MYSQL_DATABASE_DB'] = 'auctionista'
app.config['MYSQL_DATABASE_HOST'] = '127.0.0.1'
mysql.init_app(app)


# register
@app.route("/api/register", methods=["POST"])
def register():
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        query = "INSERT INTO users SET name = %s, email = %s, password = %s"
        bind = (request.json["name"],
                request.json["email"], request.json["password"])
        cursor.execute(query, bind)
        conn.commit()
        response = jsonify({"Created user ": cursor.lastrowid})
        response.status_code = 200
        return response
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


# login
@app.route("/api/login", methods=["POST"])
def login():
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        query = "SELECT * FROM users WHERE email = %s AND password = %s"
        bind = (request.json['email'], request.json['password'])
        cursor.execute(query, bind)
        user = cursor.fetchone()
        if user['email']:
            session['user'] = user
            return jsonify({"login": True})
    except Exception as e:
        return jsonify({"login": False})
    finally:
        cursor.close()
        conn.close()

# get object list


@app.route("/api/objects", methods=["GET"])
def get_objects():
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute('''SELECT objects.title, objects.info, objects.end_time, MAX(bids.amount) as current_bid
FROM objects
LEFT JOIN bids
ON objects.id = bids.object
GROUP BY objects.id''')
        rows = cursor.fetchall()
        response = jsonify(rows)
        response.status_code = 200
        return response
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

# get object category list


@app.route("/api/objects/categories/<id>", methods=["GET"])
def get_objects_by_category(id):
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        query = '''SELECT objects.title, objects.info, objects.end_time, MAX(bids.amount) as current_bid
FROM objects 
LEFT JOIN bids
ON objects.id = bids.object
WHERE objects.category = %s
GROUP BY objects.id'''
        bind = (id)
        cursor.execute(query, bind)
        rows = cursor.fetchall()
        response = jsonify(rows)
        response.status_code = 200
        return response
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

# get objects by status


@app.route("/api/objects/<status>", methods=["GET"])
def get_objects_by_status(status):
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        if status == "ongoing":
            query = '''SELECT objects.title, objects.info, objects.end_time, MAX(bids.amount) as current_bid
FROM objects 
LEFT JOIN bids
ON objects.id = bids.object
WHERE CURRENT_TIMESTAMP BETWEEN objects.start_time AND objects.end_time
GROUP BY objects.id'''
        elif status == "finished":
            query = '''SELECT objects.title, objects.info, objects.end_time, MAX(bids.amount) as current_bid
FROM objects 
LEFT JOIN bids
ON objects.id = bids.object
WHERE CURRENT_TIMESTAMP > objects.end_time
GROUP BY objects.id'''
        elif status == "sold":
            query = '''SELECT objects.title, objects.info, objects.end_time, MAX(bids.amount) as current_bid
FROM objects 
LEFT JOIN bids
ON objects.id = bids.object
WHERE CURRENT_TIMESTAMP > objects.end_time 
AND bids.amount > objects.starting_price AND bids.amount > objects.reserve_price
GROUP BY objects.id'''
        elif status == "unsold":
            query = '''SELECT objects.title, objects.info, objects.end_time, MAX(bids.amount) as current_bid
FROM objects 
LEFT JOIN bids
ON objects.id = bids.object
WHERE CURRENT_TIMESTAMP BETWEEN objects.start_time AND objects.end_time
OR (CURRENT_TIMESTAMP > objects.end_time AND bids.amount < objects.reserve_price)
GROUP BY objects.id'''
        cursor.execute(query)
        rows = cursor.fetchall()
        response = jsonify(rows)
        response.status_code = 200
        return response
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

# get object details


@app.route("/api/objects/<id>", methods=["GET"])
def get_object_details(id):
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        query = "SELECT * FROM objects WHERE objects.id = %s"
        query2 = "SELECT * FROM bids WHERE bids.object = %s ORDER BY bids.amount DESC LIMIT 5"
        bind = (id)
        cursor.execute(query, bind)
        rows = cursor.fetchall()
        cursor.execute(query2, bind)
        rows2 = cursor.fetchall()
        response = jsonify([rows, rows2])
        response.status_code = 200
        return response
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

# create new object


@app.route("/api/objects", methods=["POST"])
def create_object():
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        user = session["user"]["id"]
        query = '''INSERT INTO objects 
SET title = %s, 
start_time = %s, 
end_time = %s, 
description = %s, 
poster = %s, 
info = %s, 
starting_price = %s, 
reserve_price = %s,
category = %s'''
        if request.json["start_time"]:
            start_time = request.json["start_time"]
        else:
            start_time = datetime.now()
        print(start_time)
        bind = (request.json["title"],
                start_time,
                request.json["end_time"],
                request.json["description"],
                user,
                request.json["info"],
                request.json["starting_price"],
                request.json["reserve_price"],
                request.json["category"])
        if user is not None:
            cursor.execute(query, bind)
            conn.commit()
            response = jsonify({"Created object ": cursor.lastrowid})
            response.status_code = 200
            return response
        else:
            return jsonify("Error: User is not logged in.")
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

# create bid


@app.route("/api/objects/<id>/bid", methods=["POST"])
def create_bid(id):
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        user = session["user"]["id"]
        cursor.execute(
            f"SELECT objects.poster FROM objects WHERE objects.id = {id} ")
        seller = cursor.fetchone()
        cursor.execute(
            f"SELECT MAX(bids.amount) AS current_bid FROM bids WHERE bids.object = {id}")
        current_bid = cursor.fetchone()
        new_bid = request.json["amount"]
        query = "INSERT INTO bids SET bids.user = %s, bids.object = %s, bids.amount = %s, bids.date= CURRENT_TIMESTAMP"
        bind = (user, id, new_bid)
        if user is not None:
            if user != seller['poster']:
                if new_bid > current_bid['current_bid']:
                    cursor.execute(query, bind)
                    conn.commit()
                    response = jsonify({"Created bid ": cursor.lastrowid})
                    response.status_code = 200
                    return response
                else:
                    return jsonify(f"Error: Bid is too low, your bid needs to be higher than {current_bid['current_bid']}")
            else:
                return jsonify("Error: You cannot bid on your own item!")
        else:
            return jsonify("Error: User is not logged in.")
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

# view posted items


@app.route("/api/user/objects", methods=["GET"])
def get_user_objects():
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        user = session["user"]["id"]
        query = f'''SELECT objects.title, objects.info, objects.end_time, MAX(bids.amount) as current_bid
FROM objects 
LEFT JOIN bids
ON objects.id = bids.object 
WHERE OBJECTS.POSTER = {user}
GROUP BY objects.id'''
        if user is not None:
            cursor.execute(query)
            rows = cursor.fetchall()
            response = jsonify(rows)
            response.status_code = 200
            return response
        else:
            return jsonify("Error: User is not logged in.")
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

# get bidded objects


@app.route("/api/user/objects/bidded", methods=["GET"])
def get_bidded_objects():
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        user = session["user"]["id"]
        query = f'''SELECT objects.title, objects.info, objects.end_time, MAX(bids.amount) as current_bid
FROM objects 
LEFT JOIN bids
ON objects.id = bids.object 
WHERE objects.id IN 
	(SELECT bids.object FROM bids WHERE bids.user = {user})
GROUP BY objects.id;'''
        if user is not None:
            cursor.execute(query)
            rows = cursor.fetchall()
            response = jsonify(rows)
            response.status_code = 200
            return response
        else:
            return jsonify("Error: User is not logged in.")
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

# get searched objects


@app.route("/api/search/<term>", methods=["GET"])
def get_searched_objects(term):
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        query = f'''SELECT objects.title, objects.info, objects.end_time, MAX(bids.amount) as current_bid
FROM objects 
LEFT JOIN bids
ON objects.id = bids.object 
WHERE objects.title LIKE '%{term}%' 
OR objects.info LIKE '%{term}%' 
OR objects.description LIKE '%{term}%'
GROUP BY objects.id'''
        cursor.execute(query)
        rows = cursor.fetchall()
        response = jsonify(rows)
        response.status_code = 200
        return response
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

# get searched objects by category


@app.route("/api/category/<id>/search/<term>", methods=["GET"])
def get_searched_objects_by_category(term, id):
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        query = f'''SELECT objects.title, objects.info, objects.end_time, MAX(bids.amount) as current_bid
FROM objects 
LEFT JOIN bids
ON objects.id = bids.object 
WHERE (objects.title LIKE '%{term}%' 
OR objects.info LIKE '%{term}%' 
OR objects.description LIKE '%{term}%')
AND category = {id}
GROUP BY objects.id'''
        cursor.execute(query)
        rows = cursor.fetchall()
        response = jsonify(rows)
        response.status_code = 200
        return response
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

# rating a seller


@app.route("/api/object/<id>/rate", methods=["POST"])
def rate_seller(id):
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        user = session["user"]["id"]
        cursor.execute(
            f"SELECT objects.poster FROM objects WHERE objects.id = {id} ")
        seller = cursor.fetchone()
        query = "INSERT INTO ratings SET ratings.rating = %s, ratings.user = %s"
        bind = (request.json["rating"], seller["poster"])
        if user is not None:
            if user != seller['poster']:
                cursor.execute(query, bind)
                conn.commit()
                response = jsonify({"Added Rating ": cursor.lastrowid})
                response.status_code = 200
                # UPDATE AVERAGE RATING ON USER TABLE
                return response
            else:
                return jsonify("Error: You cannot rate yourself!")
        else:
            return jsonify("Error: User is not logged in.")
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

# see user information


@app.route("/api/user/<id>", methods=["GET"])
def get_user_details(id):
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        query = "SELECT * FROM users WHERE users.id = %s"
        query2 = "SELECT ROUND(AVG(ratings.rating), 1) AS rating FROM ratings WHERE ratings.user = %s"
        bind = (id)
        cursor.execute(query, bind)
        info = cursor.fetchone()
        cursor.execute(query2, bind)
        rating = cursor.fetchone()
        response = jsonify([info, rating])
        response.status_code = 200
        return response
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

# send message to user


@app.route("/api/user/<id>/chat", methods=["POST"])
def send_message(id):
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        user = session["user"]["id"]
        query = '''INSERT INTO messages SET 
sender = %s, receiver = %s,
message = %s, 
timestamp = CURRENT_TIMESTAMP'''
        bind = (user, id, request.json["message"])
        if user is not None:
            cursor.execute(query, bind)
            conn.commit()
            response = jsonify({"Message sent ": cursor.lastrowid})
            response.status_code = 200
            return response
        else:
            return jsonify("Error: User is not logged in.")
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

# see chat


@app.route("/api/user/<id>/chat", methods=["GET"])
def see_chat(id):
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        user = session["user"]["id"]
        query = f'''SELECT * FROM messages 
WHERE (sender = {user} AND receiver = {id}) 
OR (sender = {id} AND receiver = {user})
ORDER BY messages.timestamp ASC'''
        if user is not None:
            cursor.execute(query)
            rows = cursor.fetchall()
            response = jsonify([rows])
            response.status_code = 200
            return response
        else:
            return jsonify("Error: User is not logged in.")
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


app.run()
