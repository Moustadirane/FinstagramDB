#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import hashlib
import time
import datetime as dt

SALT = 'randomDatabases'

#Initialize the app from Flask
app = Flask(__name__)
app.debug = True

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       port = 8889,
                       user='root',
                       password='root',
                       db='Finstagram',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

#Define a route to hello function
@app.route('/')
def hello():
    return render_template('index.html')


@app.route('/home')
def home():

    user = session['username']

    return render_template('home.html', username = user)
    ##posts is some list of lists
    ##home.html will iterate through all the data returned from our query

#Define route for login
@app.route('/login')
def login():
    return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
    return render_template('register.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password'] + SALT
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM Person WHERE username = %s and password = %s'


    cursor.execute(query, (username, hashed_password))
    ###stores the results in a variable
    data = cursor.fetchone()

    ###use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    if(data):
        #creates a session for the the user
        #session is a built in
        ##session['username'] = username
        session['username'] = data['username']
        return redirect(url_for('home'))
    else:
        #returns an error message to the html page
        error = 'Invalid login or username. Please try again.'
        return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #cursor used to send queries
    cursor = conn.cursor()

    if(request.form):
        username = request.form['username']
        password = request.form['password'] + SALT
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        email = request.form['email']
        hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

        try:
            query = 'INSERT INTO Person VALUES(%s,%s,%s,%s,%s)'
            cursor.execute(query, (username, hashed_password, firstName, lastName, email))

            if (cursor.fetchone()):
                error = "This user already exists"
                return render_template('register.html', error = error)
            else:
                conn.commit()
                cursor.close()
                return render_template('index.html')

        except pymysql.err.IntegrityError:
            error = "This username is taken."
            return render_template('register.html', error = error)
    else:
        error = "Some error occurred"
        return render_template('register.html', error = error)


@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')

def run_sql_one(query, data):
    cursor = conn.cursor()
    cursor.execute(query, data)
    data = cursor.fetchone()
    cursor.close()
    return data

#Feature 1

@app.route('/images')
def show_images():
    username = session['username']
    cursor = conn.cursor()

    currentTime = time.time()
    ts = dt.datetime.fromtimestamp(currentTime).strftime('%Y-%m-%d %H: %M: %S')#timestamp

    #Query to get all images a user has access to
    #Images that they POST

    user_post = 'CREATE VIEW user_post as (SELECT DISTINCT pID, \
    postingDate,filePath, allFollowers, caption, poster FROM Photo WHERE poster = %s) '
    cursor.execute(user_post, (username))

    #Images that the people they are following POST
    following_post = 'CREATE VIEW following_post as (SELECT DISTINCT pID, \
    postingDate,filePath, allFollowers, caption, poster FROM Photo JOIN Follow\
    ON (poster = followee) WHERE follower = %s AND followStatus = TRUE)'
    cursor.execute(following_post,  (username))

    #Images that have been shared with them in a friend group
    shared_image = 'CREATE VIEW shared_image as (SELECT DISTINCT pID, \
    postingDate,filePath, allFollowers, caption, poster FROM Photo NATURAL JOIN SharedWith\
    WHERE (%s, groupName) IN (SELECT username, groupName FROM BelongTo) )'
    cursor.execute(shared_image, (username))

    query = 'SELECT * FROM user_post UNION (SELECT * FROM following_post) \
    UNION (SELECT * FROM shared_image) ORDER BY postingDate DESC'



    cursor.execute(query)

    info = cursor.fetchall()

    query = 'DROP VIEW user_post, following_post, shared_image'
    cursor.execute(query)

    personsTagged = ' SELECT * FROM Tag NATURAL JOIN Photo NATURAL JOIN Person \
    WHERE tagStatus = True;'

    react = 'SELECT username, comment, emoji FROM ReactTo'

    cursor.close()

    return render_template('images.html', data = info, username = username )

#Feature 2
#
#@app.route('/post', methods = ['GET', 'POST'])
#def post_image():
#    username = session['username']
#    cursor = conn.cursor()
#    photo = request.form['photo']
#    query = 'INSERT INTO Photo(pID, postingDate,filePath, allFollowers, caption, poster) \
#    VALUES(%s,%s, %s,%s,%s, %s)'
#    cursor.execute(query(photo, username))
#    conn.commit()
#    cursor.close()
#    return redirect(url_for('home'))
#Feature 3

#Feature 4

#Feature 5

app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
