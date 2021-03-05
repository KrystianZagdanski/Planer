from flask import Flask, render_template, url_for, redirect, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# create app
app = Flask(__name__)
# init database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# constant
COLORS = {'Blue': '#268AFF',
          'Gray': '#D1DBDA',
          'Green': '#9EC545',
          'Red': '#DB5F40',
          'Orange': '#EC8C32',
          'Light Blue': '#92C8E8'}
STATUSES = {'TODO': COLORS['Blue'],
            'In progress': COLORS['Orange'],
            'Failed': COLORS['Red'],
            'Done': COLORS['Green']}


# create table model
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey('list.id'), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    content = db.Column(db.String)
    status = db.Column(db.String(32), default='TODO')


class List(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), default='New List')
    color = db.Column(db.String(32), default='Blue')
    tasks = db.relationship('Task', backref='list', lazy=True)


# routes
@app.route('/')
def index():

    try:
        lists = List.query.order_by(List.id).all()
        return render_template('index.html', lists=lists, statuses=STATUSES, colors=COLORS)
    except:
        return "Cant get data from db"


@app.route('/add/list')
def add_list():
    new_list = List()
    try:
        db.session.add(new_list)
        db.session.commit()
        return render_template('list.html', list=new_list, colors=COLORS)
    except:
        return "Something went wrong while adding list!"


@app.route('/add/task/<int:id>')
def add_task(id):
    new_task = Task(title='New Task', content='', list_id=id)
    try:
        db.session.add(new_task)
        db.session.commit()
        return render_template('task.html', task=new_task, statuses=STATUSES)
    except:
        return "Something went wrong while adding task!"


@app.route('/delete/task/<int:id>')
def delete_task(id):
    my_task = Task.query.get_or_404(id)
    try:
        db.session.delete(my_task)
        db.session.commit()
        return redirect('/')
    except:
        return "Cannot delete task!"


@app.route('/delete/list/<int:id>')
def delete_list(id):
    my_list = List.query.get_or_404(id)
    try:
        Task.query.filter_by(list_id=id).delete()
        db.session.delete(my_list)
        db.session.commit()
        return redirect('/')
    except:
        return "Cannot delete list!"


@app.route('/move/<int:id>/<list_id>')
def move(id, list_id):
    my_task = Task.query.get_or_404(id)
    my_task.list_id = list_id
    try:
        db.session.commit()
        return redirect('/')
    except:
        return "Cannot move!"


@app.route('/task/<int:id>')
def goto_task(id):
    my_task = Task.query.get_or_404(id)
    return render_template('task.html', task=my_task, statuses=STATUSES)


@app.route('/list/<int:id>')
def goto_list(id):
    my_list = List.query.get_or_404(id)
    return render_template('list.html', list=my_list, colors=COLORS)


@app.route('/update/task/<int:id>', methods=['POST'])
def update_task(id):
    my_task = Task.query.get_or_404(id)
    my_task.content = request.form['content']
    my_task.title = request.form['title']
    my_task.status = request.form['status']
    try:
        db.session.commit()
        return redirect('/')
    except:
        return "Cannot update task!"


@app.route('/update/list/<int:id>', methods=['POST'])
def update_list(id):
    my_list = List.query.get_or_404(id)
    my_list.name = request.form['name']
    my_list.color = request.form['color']
    try:
        db.session.commit()
        return redirect('/')
    except:
        return "Cannot update list!"


if __name__ == '__main__':
    app.run(debug=True)