import json
import os
import random

from flask import Flask, render_template, abort, request, redirect, url_for, session
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect, CSRFError
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


def get_teachers_by_price(r=False):
    with open("data/teachers.json") as f:
        teachers = json.load(f)
    result = sorted(teachers, key=lambda x: x['price'], reverse=r)
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


@app.errorhandler(CSRFError)
def handle_csrf_error(_):
    return "И кто это тут у нас про CSRF token забыл?", 400


@app.route("/")
def render_main():
    goals, teachers = get_goals(), get_six_random_teachers()
    return render_template("index.html", goals=goals,
                           teachers=teachers)


@app.route("/all/")
def render_all():
    form = SortForm(request.args, meta={'csrf': False})

    if form.validate() or not request.args.to_dict():
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
            teachers = get_teachers_by_price(True)
            return render_template("all.html", form=form,
                                   teachers=teachers)

        elif sort_value == "cheap_first":
            teachers = get_teachers_by_price()
            return render_template("all.html", form=form,
                                   teachers=teachers)

    else:
        return redirect(url_for("render_all"))


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
    goals, teachers = get_goals(), get_teachers()

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

    if form.validate_on_submit():
        goal_choices = dict(form.goal.choices)
        time_choices = dict(form.time.choices)
        session['request_goal'] = form.goal.data
        session['request_goal_label'] = goal_choices[form.goal.data]
        session['request_time'] = form.time.data
        session['request_time_label'] = time_choices[form.time.data]
        session['request_client_name'] = form.client_name.data
        session['request_client_phone'] = form.client_phone.data

        rec = {"goal": session['request_goal'],
               "time": session['request_time'],
               "name": session['request_client_name'],
               "phone": session['request_client_phone']}
        add_record("data/request.json", rec)
        return redirect(url_for("render_request_done"))
    else:
        return render_template("request.html", form=form)


@app.route("/request_done/")
def render_request_done():
    return render_template("request_done.html", goal=session['request_goal_label'],
                           time=session['request_time_label'],
                           name=session['request_client_name'],
                           phone=session['request_client_phone'])


@app.route("/booking/<int:teacher_id>/<day>/<time>/", methods=["GET", "POST"])
def render_booking(teacher_id, day, time):
    # return f"Здесь будет форма бронирования преподавателя {teacher_id} на день недели {day} и время {time}"
    goals, teacher = get_goals(), get_teacher_by_id(teacher_id)
    schedule = get_schedule(teacher)

    if schedule.get(days[day][1]) and f"{time}:00" in schedule.get(days[day][1]):
        form = BookingForm()
        if form.validate_on_submit():
            session['booking_day'] = form.weekday.data
            session['booking_time'] = form.time.data
            session['booking_teacher_id'] = form.teacher.data
            session['booking_client_name'] = form.client_name.data
            session['booking_client_phone'] = form.client_phone.data

            rec = {"day": session['booking_day'],
                   "time": session['booking_time'],
                   "teacher": session['booking_teacher_id'],
                   "name": session['booking_client_name'],
                   "phone": session['booking_client_phone']}
            add_record("data/booking.json", rec)
            return redirect(url_for("render_booking_done"))

        else:
            return render_template("booking.html", form=form,
                                   teacher=teacher,
                                   days=days,
                                   day=day,
                                   time=time)
    abort(404)


@app.route("/booking_done/")
def render_booking_done():
    return render_template("booking_done.html", days=days,
                           day=session['booking_day'],
                           time=session['booking_time'],
                           name=session['booking_client_name'],
                           phone=session['booking_client_phone'])


if __name__ == '__main__':
    app.run()
