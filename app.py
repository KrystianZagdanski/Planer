""" Listable web app """
from flask import Flask, render_template, redirect, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
import bcrypt
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import InputRequired, Length, Regexp, Email

# create and configure app
app = Flask(__name__)
app.config['SECRET_KEY'] = '7n1cn1c721yc1yn10c1@!!$12v1813VFDH%@%4324'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

# constant
STATUSES = {'TODO': '#268AFF',
            'In progress': '#EC8C32',
            'Failed': '#DB5F40',
            'Done': '#9EC545'}


# create table models
class Task(db.Model):
    """
    Class representing Task table in database.

    :type id: int
    :type list_id: int
    :type title: str
    :type content: str
    :type status: str
    """
    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey('list.id'), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    content = db.Column(db.String)
    status = db.Column(db.String(32), default='TODO')


class List(db.Model):
    """
    Class representing List table in database.

    :type id: int
    :type user_id: int
    :type name: str
    :type color: str
    :type tasks: list[Task]
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(64), default='New List')
    color = db.Column(db.String(7), default='#268AFF')
    tasks = db.relationship('Task', backref='list', lazy=True)


class User(db.Model, UserMixin):
    """
    Class representing User table in database.

    :type id: int
    :type username: str
    :type password: str
    :type lists: list[List]
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    lists = db.relationship('List', backref='user', lazy=True)


# create form models
class LoginForm(FlaskForm):
    """
    Model for login form.

    :type username: str
    :type password: str
    """
    username = StringField("Username", validators=[InputRequired()],
                           render_kw={"placeholder": "Username", "class": "form-control"})
    password = PasswordField("Password", validators=[InputRequired()],
                             render_kw={"placeholder": "Password", "class": "form-control"})


class RegisterForm(FlaskForm):
    """
    Model for register form.

    :type username: str
    :type email: str
    :type password: str
    """
    username = StringField("Username", validators=[InputRequired(), Length(min=3, max=32),
                           Regexp(regex=r'^\w+$',
                                  message="Username can contain only letters, numbers and underscore.")],
                           render_kw={"placeholder": "Username", "class": "form-control"})
    email = StringField("Email", validators=[InputRequired(), Email("Incorrect email."), Length(min=1, max=120)],
                        render_kw={"placeholder": "Email", "class": "form-control"})
    password = PasswordField("Password",
                             validators=[InputRequired(), Length(min=8, max=64)],
                             render_kw={"placeholder": "Password", "class": "form-control"})


@login_manager.user_loader
def load_user(user_id):
    """
    Load user data.

    :param int user_id: id of user
    :return: Logged in user
    :rtype: User
    """
    return User.query.get(int(user_id))


# routes
@app.route('/')
def index():
    """
    Renders main page.

    :return: Rendered index.html page.
    """
    return render_template('index.html')


@app.route('/my_lists')
@login_required
def my_lists():
    """
    Renders my_lists page. Requires user to be logged in.

    :return: Rendered my_lists.html page.
    """
    try:
        lists = List.query.filter_by(user_id=current_user.id).all()
        return render_template('my_lists.html', lists=lists, statuses=STATUSES)
    except SQLAlchemyError as exc:
        return f"{type(exc).__name__} occurred while getting lists from database:</br>{exc}"


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    On GET method, renders login page.
    On POST try to login user.
    If user is successfully logged in, renders my_lists page otherwise renders login page with message.

    :return: Rendered login.html page or redirect to /my_lists.
    """
    if current_user.is_authenticated:
        return redirect('/my_lists')

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data.encode("utf-8")
        user = User.query.filter_by(username=username).first()
        if user:
            if bcrypt.checkpw(password, user.password):
                login_user(user)
                return redirect('/my_lists')

        return render_template('login.html', form=form, message="Incorrect Username or Password.")

    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    """
    Log out current user.

    :return: Redirect to root /.
    """
    logout_user()
    return redirect('/')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    On GET method, renders register page.
    On POST method: Check if username isn't taken and try to create new user.
    If new user was successfully created then it's logged in and redirected to my_lists page.
    Otherwise print error message and renders register page with message.

    :return: Rendered register.html page or redirect to /my_lists.
    """
    if current_user.is_authenticated:
        return redirect('/my_lists')

    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data.encode("utf-8")
        if not User.query.filter_by(username=username).first():
            new_user = User(username=username, email=email, password=bcrypt.hashpw(password, bcrypt.gensalt()))
            try:
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
                return redirect('/my_lists')
            except SQLAlchemyError as exc:
                print(f"{type(exc).__name__} occurred while trying to push new user into database:</br>{exc}")
        else:
            return render_template('register.html', form=form, message='Name already taken!')

    return render_template('register.html', form=form)


@app.route('/add/list')
@login_required
def add_list():
    """
    Create new list in database and renders list page.

    :return: Rendered list.html page or str.
    """
    new_list = List(user_id=current_user.id)
    try:
        db.session.add(new_list)
        db.session.commit()
        return render_template('list.html', list=new_list)
    except SQLAlchemyError as exc:
        return f"{type(exc).__name__} occurred while adding new list into database:</br>{exc}"


@app.route('/add/task/<int:list_id>')
@login_required
def add_task(list_id):
    """
    Create new task in database and renders task page.

    :param int list_id: Id of a list.
    :return: Rendered task.html page or str.
    """
    if not List.query.get(list_id) in current_user.lists:
        return redirect('/my_lists')

    new_task = Task(title='New Task', content='', list_id=list_id)
    try:
        db.session.add(new_task)
        db.session.commit()
        return render_template('task.html', task=new_task, statuses=STATUSES)
    except SQLAlchemyError as exc:
        return f"{type(exc).__name__} occurred while adding new task into database:</br>{exc}"


@app.route('/delete/task/<int:task_id>')
@login_required
def delete_task(task_id):
    """
    Deletes task from database.

    :param int task_id: Id of a task.
    :return: Redirect to /my_lists or str.
    """
    my_task = Task.query.get_or_404(task_id)
    if not List.query.get(my_task.list_id) in current_user.lists:
        return redirect('/my_lists')

    try:
        db.session.delete(my_task)
        db.session.commit()
        return redirect('/my_lists')
    except SQLAlchemyError as exc:
        return f"{type(exc).__name__} occurred while deleting task from database:</br>{exc}"


@app.route('/delete/list/<int:list_id>')
@login_required
def delete_list(list_id):
    """
    Deletes list and all tasks in it from database.

    :param int list_id: Id of a list.
    :return: Redirect to /my_lists or str.
    """
    my_list = List.query.get_or_404(list_id)
    if my_list not in current_user.lists:
        return redirect('/my_lists')

    try:
        Task.query.filter_by(list_id=list_id).delete()
        db.session.delete(my_list)
        db.session.commit()
        return redirect('/my_lists')
    except SQLAlchemyError as exc:
        return f"{type(exc).__name__} occurred while deleting list and tasks from database:</br>{exc}"


@app.route('/move/<int:task_id>/<int:list_id>')
@login_required
def move(task_id, list_id):
    """
    Move task to another list.

    :param int task_id: Id of a task.
    :param int list_id: Id of a list.
    :return: Redirect to /my_lists or str.
    """
    my_task = Task.query.get_or_404(task_id)
    if not List.query.get(my_task.list_id) in current_user.lists:
        return redirect('/my_lists')

    my_task.list_id = list_id
    try:
        db.session.commit()
        return redirect('/my_lists')
    except SQLAlchemyError as exc:
        return f"{type(exc).__name__} occurred while updating task in database:</br>{exc}"


@app.route('/task/<int:task_id>')
@login_required
def goto_task(task_id):
    """
    Renders task page.

    :param int task_id: Id of a task.
    :return: Rendered task.html page or redirect to /my_lists.
    """
    my_task = Task.query.get_or_404(task_id)
    if not List.query.get(my_task.list_id) in current_user.lists:
        return redirect('/my_lists')

    return render_template('task.html', task=my_task, statuses=STATUSES)


@app.route('/list/<int:list_id>')
@login_required
def goto_list(list_id):
    """
    Renders list page.

    :param int list_id: Id of a list.
    :return: Rendered list.html page or redirect to /my_lists.
    """
    my_list = List.query.get_or_404(list_id)
    if my_list not in current_user.lists:
        return redirect('/my_lists')

    return render_template('list.html', list=my_list)


@app.route('/update/task/<int:task_id>', methods=['POST'])
@login_required
def update_task(task_id):
    """
    Update task and redirect to my_lists page.

    :param int task_id: Id of a task.
    :return: Redirect to /my_lists or str.
    """
    my_task = Task.query.get_or_404(task_id)
    if List.query.get(my_task.list_id) not in current_user.lists:
        return redirect('/my_lists')

    my_task.content = request.form['content']
    my_task.title = request.form['title']
    my_task.status = request.form['status']
    try:
        db.session.commit()
        return redirect('/my_lists')
    except SQLAlchemyError as exc:
        return f"{type(exc).__name__} occurred while updating task in database:</br>{exc}"


@app.route('/update/list/<int:list_id>', methods=['POST'])
@login_required
def update_list(list_id):
    """
    Update list and redirect to my_lists page.

    :param int list_id: Id of a list.
    :return: Redirect to /my_lists or str.
    """
    my_list = List.query.get_or_404(list_id)
    if my_list not in current_user.lists:
        return redirect('/my_lists')

    my_list.name = request.form['name']
    my_list.color = request.form['color']
    try:
        db.session.commit()
        return redirect('/my_lists')
    except SQLAlchemyError as exc:
        return f"{type(exc).__name__} occurred while updating list in database:</br>{exc}"


if __name__ == '__main__':
    app.run(debug=True)
