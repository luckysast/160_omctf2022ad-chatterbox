import os
import jwt
import datetime
from model import *
from utils import *
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask import Flask, redirect, render_template, request, make_response, render_template_string

app = Flask(__name__, static_url_path='', static_folder='static/')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatterbox.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(16).hex()

app.config['PRIVATE_KEY'] = open('/root/key', 'r').read()
app.config['PUBLIC_KEY'] = open('/root/key.pub', 'r').read()

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

@app.route("/")
def index():
    try:
        user = jwt.decode(request.cookies.get('session'), app.config['PUBLIC_KEY'], algorithms=["RS256"])
        columns = ['id', 'sender_id', 'recipient_id', 'message', 'time']
        sender_data = Message.query.filter_by(sender_id=user['id']).all()
        messages = as_dict(sender_data, columns)
        recipient_data = Message.query.filter_by(recipient_id=user['id']).all()
        messages += as_dict(recipient_data, columns)
        if messages != []:
            messages.sort(key=lambda mes: mes['id'], reverse=True)
            results = last_messages(messages, user['id'])
            for result in results:
                if result['sender_id'] != user['id']:
                    result['username'] = User.query.filter_by(id=result['sender_id']).first().username
                    result['user_id'] = result['sender_id']
                elif result['recipient_id'] != user['id']:
                    result['username'] = User.query.filter_by(id=result['recipient_id']).first().username
                    result['user_id'] = result['recipient_id']
                if len(result['message'].split(' ')) > 25:
                    result['message'] = ' '.join([result['message'].split(' ')[i] for i in range(25)])+'...'
            if results != []:
                return render_template_string(render_template('index.html', messages=results, username=user['username']))
        return render_template_string(render_template('index.html', msg=True, username=user['username']))
    except:
        return render_template_string(render_template('index.html',index=True))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if len(password) <=8:
            msg = "Use a password of at least 8 characters"
            return render_template_string(render_template('register.html', msg=msg))
        user = User.query.filter_by(username=username).first()
        if user:
            msg = 'Username already exists'
            return render_template_string(render_template('register.html', msg=msg))
        new_user = User(username=username, password=bcrypt.generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit() 
        result = as_dict([User.query.filter_by(username=username).first()], ['id', 'username'])
        token = jwt.encode(result[0], app.config['PRIVATE_KEY'], algorithm="RS256")
        response = make_response(redirect('/'))
        response.set_cookie('session', token)
        return response
    if request.method == 'GET':
        try:
            user = jwt.decode(request.cookies.get('session'), app.config['PUBLIC_KEY'], algorithms=["RS256"])
            return redirect('/')
        except:
            return render_template_string(render_template("register.html"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if not user or not bcrypt.check_password_hash(user.password, password):
            msg = 'The username or password is incorrect.'
            return render_template_string(render_template('login.html', msg=msg))
        result = as_dict([user], ['id', 'username'])
        token = jwt.encode(result[0], app.config['PRIVATE_KEY'], algorithm="RS256")
        response = make_response(redirect('/'))
        response.set_cookie('session', token)
        return response
    if request.method == 'GET':
        try:
            user = jwt.decode(request.cookies.get('session'), app.config['PUBLIC_KEY'], algorithms=["RS256"])
            return redirect('/')
        except:
            return render_template_string(render_template('login.html'))

@app.route("/logout")
def logout():
    response = make_response(redirect('/login'))
    response.set_cookie('session', '', expires=0)
    return response

@app.route("/users", methods=["GET"])
def users():
    try:
        user = jwt.decode(request.cookies.get('session'), app.config['PUBLIC_KEY'], algorithms=["RS256"])
        users = as_dict(User.query.all(), ['id', 'username'])
        users.pop(user['id']-1)
        return render_template_string(render_template('users.html', users=users, username=user['username']))
    except:
        return redirect('/login')

@app.route('/users/<int:id>', methods=['POST', 'GET'])
def user_messages(id):
    if request.method == 'POST':
        message = request.form.get('message')
        user = jwt.decode(request.cookies.get('session'), app.config['PUBLIC_KEY'], algorithms=["RS256"])
        time = datetime.datetime.now().strftime('%H:%M:%S')
        try:
            if user['id'] != id:
                new_message = Message(sender_id=User.query.filter_by(username=user['username']).first(
                ).id, recipient_id=id, message=message, time=time)
                db.session.add(new_message)
                db.session.commit()
                return redirect('/users/'+str(id))
            else:
                return redirect('/')
        except:
            return redirect('/')
    if request.method == 'GET':
        try:
            user = jwt.decode(request.cookies.get('session'), app.config['PUBLIC_KEY'], algorithms=["RS256"])
            user_name = User.query.filter_by(id=id).first().username
            columns = ['id', 'sender_id', 'recipient_id', 'message', 'time']
            messages = as_dict(Message.query.filter_by(sender_id=user['id'], recipient_id=id).all(), columns)
            messages += as_dict(Message.query.filter_by(sender_id=id, recipient_id=user['id']).all(), columns)
            if messages != []:
                messages.sort(key=lambda mes: mes['id'], reverse=False)
                for message in messages:
                    if message['sender_id'] != user['id']:
                        message['receive'] = True
                    elif message['recipient_id'] != user['id']:
                        message['receive'] = False
                return render_template_string(render_template('messages.html', messages=messages, user=user_name, username=user['username']))
            if user['id'] != id:
                return render_template_string(render_template('messages.html', msg=True, user=user_name, username=user['username']))
            else:
                return redirect('/')
        except:
            return redirect('/login')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
