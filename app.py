from flask import Flask, render_template,request, redirect,flash,session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_mail import Mail, Message
from random import randint

import pymysql

app = Flask(__name__)
app.secret_key = 'krish'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:admin@localhost/inter'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USERNAME"] = "kr8123965@gmail.com"
app.config["MAIL_PASSWORD"] = "nlsy nevs zxqd ltkk"
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True
mail = Mail(app)

db = SQLAlchemy(app)

class Todo(db.Model):
    __tablename__ = 'task_manager'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    task_assigned_to = db.Column(db.String(200), nullable=False)
    task_assigned_by = db.Column(db.String(200), nullable=False)
    completed_by = db.Column(db.DateTime)
    date_created = db.Column(db.DateTime, default=datetime.now)
    review = db.Column(db.String(200), nullable=True)
    
    def __repr__(self):
        return f'<Task {self.id}>'

class Auth(db.Model):
    __tablename__ = 'auth1'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f'<Auth {self.id}>'

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form.get("username", False)
        password = request.form.get("password", False)
        email = request.form.get("email", False)
        if not username or not password or not email:
            flash('Username, password, and email are required.')
        existing_user = Auth.query.filter_by(username=username).first()
        if existing_user:
            return render_template('sign_up_error.html')
        else:
            user = Auth(username=username, password=password, email=email)
            try:
                db.session.add(user)
                db.session.commit()
                return redirect('/')
            except Exception as e:
                return f'There is an error in creating user: {e}'
    else:
        return render_template('signup.html')

@app.route('/', methods=['POST', 'GET'])
def home():
    if request.method == 'POST':
        username = request.form.get("username", False)
        password = request.form.get("password", False)
        existing_user = Auth.query.filter_by(username=username, password=password).first()
        if existing_user:
            email1 = existing_user.email
            msg = Message(subject='OTP', sender='kr8123965@gmail.com', recipients=[email1])
            otp = randint(000000, 999999)
            session['otp']=otp
            msg.body = str(otp)
            mail.send(msg)
            return render_template('verify.html')
        else:
            return render_template('error.html')
    else:
        return render_template('home.html')

@app.route('/verify', methods=['POST', 'GET'])
def verify():
    if request.method == 'POST':
        user_otp = request.form.get("otp", False)
        otp=session.get('otp')
        if otp == int(user_otp):
            tasks = Todo.query.all()
            return render_template("index.html", tasks=tasks)
        else:
            return render_template("verify.html")
    else:
        return render_template("verify.html")

@app.route('/index', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        task_content = request.form['content']
        task_assigned_to = request.form['assigned_to']
        task_assigned_by = request.form['assigned_by']
        completed_by = request.form['completion_time']
        review=request.form['review']
        new_task = Todo(content=task_content, task_assigned_to=task_assigned_to,
                        task_assigned_by=task_assigned_by, completed_by=completed_by,review=review)
        try:
            db.session.add(new_task)
            db.session.commit()
            return redirect('/index')
        except Exception as e:
            return f'There was an issue in adding your task: {e}'
    else:
        tasks = Todo.query.all()
        return render_template('index.html', tasks=tasks)

@app.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete(id):
    if request.method == 'POST':
        task_to_delete = Todo.query.get_or_404(id)
        try:
            db.session.delete(task_to_delete)
            db.session.commit()
            return redirect('/index')
        except Exception as e:
            return f'There was a problem deleting: {e}'

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    task = Todo.query.get_or_404(id)
    if request.method == 'POST':
        task.content = request.form['content']
        task.task_assigned_to = request.form['assigned_to']
        task.task_assigned_by = request.form['assigned_by']
        task.completed_by = request.form['completion_time']
        task.review=request.form['review']
        try:
            db.session.commit()
            return redirect('/')
        except Exception as e:
            return f'Not able to update: {e}'
    else:
        return render_template('update.html', task=task)

if __name__ == '__main__':
    app.run(debug=True)
