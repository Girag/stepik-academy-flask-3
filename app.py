import json
import random

from flask import Flask, render_template, abort, request, redirect, url_for, session
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, HiddenField, RadioField, SelectField
from wtforms.validators import InputRequired

app = Flask(__name__)
csrf = CSRFProtect(app)
app.config['SECRET_KEY'] = "VeryVeryRandomStringForVeryVerySecurity"

days = {
    "mon": ["Понедельник", "monday"],
    "tue": ["Вторник", "tuesday"],
    "wed": ["Среда", "wednesday"],
    "thu": ["Четверг", "thursday"],
    "fri": ["Пятница", "friday"],
    "sat": ["Суббота", "saturday"],
    "sun": ["Воскресенье", "sunday"],
    "monday": ["Понедельник", "mon"],
    "tuesday": ["Вторник", "tue"],
    "wednesday": ["Среда", "wed"],
    "thursday": ["Четверг", "thu"],
    "friday": ["Пятница", "fri"],
    "saturday": ["Суббота", "sat"],
    "sunday": ["Воскресенье", "sun"]
}


def get_goals():
    with open("data/goals.json") as f:
        goals = json.load(f)
    return goals


def get_teachers():
    with open("data/teachers.json") as f:
        teachers = json.load(f)
    return teachers


def get_teachers_by_goal(goal):
    with open("data/teachers.json") as f:
        teachers = json.load(f)
    result = []
    for teacher in teachers:
        if goal in teacher['goals']:
            result.append(teacher)
    return result


def get_teacher_by_id(id):
    with open("data/teachers.json") as f:
        teachers = json.load(f)
    return teachers[id]


def get_teachers_in_random():
    with open("data/teachers.json") as f:
        teachers = json.load(f)
    random.shuffle(teachers)
    return teachers


def get_six_random_teachers():
    with open("data/teachers.json") as f:
        teachers = json.load(f)
    return random.sample(teachers, 6)


def get_teachers_by_rating():
    with open("data/teachers.json") as f:
        teachers = json.load(f)
    result = sorted(teachers, key=lambda x: x['rating'], reverse=True)
    return result


def get_teachers_by_price(reverse=False):
    with open("data/teachers.json") as f:
        teachers = json.load(f)
    result = sorted(teachers, key=lambda x: x['price'], reverse=reverse)
    return result


def get_schedule(teacher):
    schedule = {}
    for day, time in teacher['free'].items():
        free_time = []
        for hour, is_free in time.items():
            if is_free:
                free_time.append(hour)
        schedule.update({day: free_time})
    return schedule


def add_record(data_path, record):
    try:
        with open(data_path, "r") as f:
            records = json.load(f)
    except FileNotFoundError:
        records = []
    records.append(record)
    with open(data_path, "w") as f:
        json.dump(records, f, indent=4, ensure_ascii=False)


class BookingForm(FlaskForm):
    weekday = HiddenField()
    time = HiddenField()
    teacher = HiddenField()
    client_name = StringField("Ваc зовут", [InputRequired(message="Укажите ваше имя")])
    client_phone = StringField("Ваш телефон", [InputRequired(message="Укажите ваш телефон")])


class RequestForm(FlaskForm):
    goals = get_goals()
    goal = RadioField("Какая цель занятий?", choices=[(key, value[0]) for key, value in goals.items()])
    time = RadioField("Сколько времени есть?", choices=[
        ('1-2', '1-2 часа в неделю'),
        ('3-5', '3-5 часов в неделю'),
        ('5-7', '5-7 часов в неделю'),
        ('7-10', '7-10 часов в неделю')
    ])
    client_name = StringField("Ваc зовут", [InputRequired(message="Укажите ваше имя")])
    client_phone = StringField("Ваш телефон", [InputRequired(message="Укажите ваш телефон")])


class SortForm(FlaskForm):
    sort = SelectField("Сортировать", choices=[
        ('random', 'В случайном порядке'),
        ('by_rating', 'Сначала лучшие по рейтингу'),
        ('expensive_first', 'Сначала дорогие'),
        ('cheap_first', 'Сначала недорогие'),
    ])


@app.errorhandler(404)
def render_not_found(_):
    return "Ничего не нашлось! Вот неудача, отправляйтесь на главную!", 404


@app.route("/")
def render_main():
    goals = get_goals()
    teachers = get_six_random_teachers()
    return render_template("index.html", goals=goals,
                           teachers=teachers)


@app.route("/all/")
def render_all():
    form = SortForm(request.args, meta={'csrf': False})

    if not form.validate() and request.args.to_dict():
        return redirect(url_for("render_all"))

    sort_value = request.args.get("sort")
    if not sort_value or sort_value == "random":
        teachers = get_teachers_in_random()
        return render_template("all.html", form=form,
                               teachers=teachers)

    elif sort_value == "by_rating":
        teachers = get_teachers_by_rating()
        return render_template("all.html", form=form,
                               teachers=teachers)

    elif sort_value == "expensive_first":
        teachers = get_teachers_by_price(reverse=True)
        return render_template("all.html", form=form,
                               teachers=teachers)

    elif sort_value == "cheap_first":
        teachers = get_teachers_by_price()
        return render_template("all.html", form=form,
                               teachers=teachers)


@app.route("/goals/<goal>/")
def render_goals(goal):
    goals = get_goals()
    try:
        goal_name = f"{goals[goal][0][0].lower()}{goals[goal][0][1:].lower()}"
        icon = goals[goal][1]
        teachers = get_teachers_by_goal(goal)
        return render_template("goal.html", goal=goal,
                               icon=icon,
                               goal_name=goal_name,
                               teachers=teachers)
    except KeyError:
        abort(404)


@app.route("/profiles/<int:teacher_id>/")
def render_profiles(teacher_id):
    goals = get_goals()
    teachers = get_teachers()

    try:
        schedule = get_schedule(teachers[teacher_id])
        return render_template("profile.html", teacher=teachers[teacher_id],
                               goals=goals,
                               days=days,
                               schedule=schedule)
    except IndexError:
        abort(404)


@app.route("/request/", methods=["GET", "POST"])
def render_request():
    form = RequestForm(goal="travel", time="5-7")

    if not form.validate_on_submit():
        return render_template("request.html", form=form)

    goal_choices = dict(form.goal.choices)
    time_choices = dict(form.time.choices)
    session['request'] = {
        "goal": form.goal.data,
        "goal_label": goal_choices[form.goal.data],
        "time": form.time.data,
        "time_label": time_choices[form.time.data],
        "client_name": form.client_name.data,
        "client_phone": form.client_phone.data
    }

    rec = {"goal": session['request']['goal'],
           "time": session['request']['time'],
           "name": session['request']['client_name'],
           "phone": session['request']['client_phone']}
    add_record("data/request.json", rec)
    return redirect(url_for("render_request_done"))


@app.route("/request_done/")
def render_request_done():
    return render_template("request_done.html", goal=session['request']['goal_label'],
                           time=session['request']['time_label'],
                           name=session['request']['client_name'],
                           phone=session['request']['client_phone'])


@app.route("/booking/<int:teacher_id>/<day>/<time>/", methods=["GET", "POST"])
def render_booking(teacher_id, day, time):
    teacher = get_teacher_by_id(teacher_id)
    schedule = get_schedule(teacher)

    if not schedule.get(days[day][1]) or f"{time}:00" not in schedule.get(days[day][1]):
        abort(404)

    form = BookingForm()
    if not form.validate_on_submit():
        return render_template("booking.html", form=form,
                               teacher=teacher,
                               days=days,
                               day=day,
                               time=time)

    session['booking'] = {
        "day": form.weekday.data,
        "time": form.time.data,
        "teacher_id": form.teacher.data,
        "client_name": form.client_name.data,
        "client_phone": form.client_phone.data
    }

    rec = {"day": session['booking']['day'],
           "time": session['booking']['time'],
           "teacher": session['booking']['teacher_id'],
           "name": session['booking']['client_name'],
           "phone": session['booking']['client_phone']}
    add_record("data/booking.json", rec)
    return redirect(url_for("render_booking_done"))


@app.route("/booking_done/")
def render_booking_done():
    return render_template("booking_done.html", days=days,
                           day=session['booking']['day'],
                           time=session['booking']['time'],
                           name=session['booking']['client_name'],
                           phone=session['booking']['client_phone'])


if __name__ == '__main__':
    app.run()
