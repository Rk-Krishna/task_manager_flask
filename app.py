from flask import Flask, render_template, request, redirect, flash, session, url_for, Response, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_wtf import FlaskForm
from wtforms import DateTimeLocalField, StringField, PasswordField, SubmitField, DateTimeField
from wtforms.widgets import DateTimeInput
from wtforms.validators import DataRequired, Email
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from random import randint
from datetime import datetime
from fpdf import FPDF

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
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'home'
migrate = Migrate(app, db)

class User(db.Model, UserMixin):
    __tablename__ = 'auth1'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)

    def __repr__(self):
        return f'<User {self.username}>'

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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class DateTimeLocalField(DateTimeField):
    widget = DateTimeInput()

class SignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class TaskForm(FlaskForm):
    content = StringField('Content', validators=[DataRequired()])
    task_assigned_to = StringField('Assigned To', validators=[DataRequired()])
    task_assigned_by = StringField('Assigned By', validators=[DataRequired()])
    completed_by = DateTimeLocalField('Completed By', format='%Y-%m-%dT%H:%M')
    review = StringField('Review')
    submit = SubmitField('Add Task')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, password=hashed_password, email=form.email.data)
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Username already exists.', 'danger')
            return render_template('signup.html', form=form)
        else:
            db.session.add(user)
            db.session.commit()
            flash('User created successfully.', 'success')
            return redirect(url_for('home'))
    return render_template('signup.html', form=form)

@app.route('/', methods=['GET', 'POST'])
def home():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            otp = randint(000000, 999999)
            session['otp'] = otp
            msg = Message(subject='OTP', sender='kr8123965@gmail.com', recipients=[user.email])
            msg.body = str(otp)
            mail.send(msg)
            flash('OTP sent to your email.', 'success')
            return redirect(url_for('verify'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('home.html', form=form)

@app.route('/verify', methods=['GET', 'POST'])
@login_required
def verify():
    if request.method == 'POST':
        user_otp = request.form.get("otp", False)
        otp = session.get('otp')
        if otp and int(user_otp) == otp:
            flash('OTP verified successfully.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid OTP.', 'danger')
            return render_template('verify.html')
    return render_template('verify.html')

@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = TaskForm()
    if request.method == 'POST':
        new_task = Todo(
            content=form.content.data,
            task_assigned_to=form.task_assigned_to.data,
            task_assigned_by=form.task_assigned_by.data,
            completed_by=form.completed_by.data,
            review=form.review.data
        )
        db.session.add(new_task)
        db.session.commit()
        flash('Task added successfully.', 'success')
        return redirect(url_for('index'))
    tasks = Todo.query.all()
    return render_template('index.html', form=form, tasks=tasks)

@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    task_to_delete = Todo.query.get_or_404(id)
    db.session.delete(task_to_delete)
    db.session.commit()
    flash('Task deleted successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    task = Todo.query.get_or_404(id)
    form = TaskForm()
    if request.method == 'POST':
        task.content = form.content.data
        task.task_assigned_to = form.task_assigned_to.data
        task.task_assigned_by = form.task_assigned_by.data
        task.completed_by = form.completed_by.data
        task.review = form.review.data
        db.session.commit()
        flash('Task updated successfully.', 'success')
        return redirect(url_for('index'))
    elif request.method == 'GET':
        form.content.data = task.content
        form.task_assigned_to.data = task.task_assigned_to
        form.task_assigned_by.data = task.task_assigned_by
        form.completed_by.data = task.completed_by
        form.review.data = task.review
        return render_template('update.html', form=form, task=task)

@app.route('/genartor', methods=['GET'])
@login_required
def generator():
    pdf = FPDF()
    pdf.add_page()
    margin = 10
    pdf.set_left_margin(margin)
    pdf.set_right_margin(margin)
    page_width = pdf.w - 2 * margin
    col_width = page_width / 5
    pdf.set_font('Times', 'B', 14.0)
    pdf.cell(page_width, 10, 'Tasks Assigned', align='C')
    pdf.ln(10)
    pdf.set_font('Courier', '', 12)
    th = pdf.font_size + 2
    pdf.cell(7, th, "ID", border=1)
    pdf.cell(30, th, "Content", border=1)
    pdf.cell(30, th, "Assigned To", border=1)
    pdf.cell(30, th, "Assigned By", border=1)
    pdf.cell(50, th, "Completed By", border=1)
    pdf.cell(50, th, "Review", border=1)
    pdf.ln(th)
    tasks = Todo.query.all()
    for task in tasks:
        completed_by = str(task.completed_by) if task.completed_by else ""
        pdf.cell(7, th, str(task.id), border=1)
        pdf.cell(30, th, task.content, border=1)
        pdf.cell(30, th, task.task_assigned_to, border=1)
        pdf.cell(30, th, task.task_assigned_by, border=1)
        pdf.cell(50, th, completed_by, border=1)
        pdf.cell(50, th, task.review, border=1)
        pdf.ln(th)
    pdf_output = "tasks_assigned.pdf"
    pdf.output(pdf_output, 'F')

    return send_file(pdf_output, as_attachment=True, download_name='tasks_assigned.pdf', mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True)
