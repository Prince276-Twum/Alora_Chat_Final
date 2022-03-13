from flask import Flask, render_template, redirect, url_for, request
from wtforms import StringField, PasswordField, SubmitField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import LoginManager, login_user, current_user, UserMixin, logout_user, login_required
from sqlalchemy.orm import relationship
from flask_socketio import SocketIO, send, join_room, leave_room, emit
import os
import time

app = Flask(__name__)
Bootstrap(app)
app.config['WTF_CSRF_SECRET_KEY'] = "b'f\xfa\x8b{X\x8b\x9eM\x83l\x19\xad\x84\x08\xaa"

app.config["SECRET_KEY"] = os.environ.get("SECRET")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL')


# app.secret_key = "secrete"
# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///user.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


# load user
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


socketio = SocketIO(app)


# user database
class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    chart_rooms = relationship('ChartRoom', back_populates="room_owner")


class ChartRoom(db.Model):
    __tablename__ = 'chartroom'
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.String, nullable=False)
    meeting_name = db.Column(db.String, nullable=False)
    meeting_passcode = db.Column(db.String, nullable=False)
    room_owner_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    room_owner = relationship("User", back_populates="chart_rooms")


# registration forms
class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=5, max=20)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=5, max=30)])
    comfirm_password = PasswordField("Comfirm Password", validators=[EqualTo("password"), DataRequired()])
    create = SubmitField()

    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError("name has been taken")


def verify_password(form, field):
    user_login_db = User.query.filter_by(username=form.username.data).first()
    if user_login_db:
        if not check_password_hash(password=form.password.data, pwhash=user_login_db.password):
            raise ValidationError("incorrect username or Password")
    else:
        raise ValidationError("incorrect username or Password")


# login forms
class LoginForms(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), verify_password])
    password = PasswordField("Password", validators=[DataRequired(), verify_password])
    create = SubmitField(label="Sign in")

    # def validate_username(self, username):
    #     if User.query.filter_by(username=username.data).first() is None:
    #         raise ValidationError("incorrect username")


# join room passcode verification
def join_verify(form, field):
    wanted_room = ChartRoom.query.filter_by(meeting_id=form.meeting_id2.data).first()
    if wanted_room:
        if not check_password_hash(password=form.passcode2.data, pwhash=wanted_room.meeting_passcode):
            raise ValidationError("incorrect passcode or meeting id")
    else:
        raise ValidationError("incorrect passcode or meeting id")


# joining meeting form
class JoinForm(FlaskForm):
    meeting_id2 = StringField(label="Meeting ID", validators=[DataRequired(), join_verify])
    passcode2 = PasswordField(label="Passcode", validators=[DataRequired(), join_verify])
    join = SubmitField()

    # def validate_meeting_id2(self, meeting_id2):
    #     if ChartRoom.query.filter_by(meeting_id=meeting_id2.data).first() is None:
    #         raise ValidationError("There is no such room")


# creating meeting forms
class CreateForm(FlaskForm):
    meeting_id = StringField()
    meeting_name = StringField(validators=[DataRequired(), Length(min=6, max=20)], )
    meeting_passcode = PasswordField(validators=[DataRequired(), Length(min=7, max=20)])
    create = SubmitField()


db.create_all()


# registration route
@app.route('/', methods=["GET", "POST"])
def register_user():
    registration_form = RegistrationForm()
    if registration_form.validate_on_submit():
        hash_password = generate_password_hash(method="pbkdf2:sha256", salt_length=8,
                                               password=registration_form.password.data)
        new_user = User(username=registration_form.username.data, password=hash_password)
        db.session.add(new_user)
        db.session.commit()

        login_user(User.query.filter_by(username=registration_form.username.data).first())
        return redirect(url_for('menu_page'))
    return render_template("index.html", form=registration_form)


# login route
@app.route("/login", methods=["POST", "GET"])
def login_page():
    login_forms = LoginForms()
    if login_forms.validate_on_submit():
        user_details = User.query.filter_by(username=login_forms.username.data).first()
        login_user(user_details)
        return redirect(url_for('menu_page'))

    return render_template("index.html", form=login_forms, show_login=True)


# user dashboard
@app.route("/menu-page", methods=["POST", "GET"])
@login_required
def menu_page():
    create_form = CreateForm()
    join_form = JoinForm()
    user_room = ChartRoom.query.all()

    if create_form.create.data:
        if create_form.validate_on_submit():
            hash_room_passcode = generate_password_hash(method="pbkdf2:sha256",
                                                        salt_length=8,
                                                        password=create_form.meeting_passcode.data)

            new_room = ChartRoom(
                meeting_id=create_form.meeting_id.data,
                meeting_name=create_form.meeting_name.data,
                meeting_passcode=hash_room_passcode,
                room_owner=current_user)
            db.session.add(new_room)
            db.session.commit()
            return redirect(url_for('menu_page'))
    elif join_form.join.data:
        if join_form.validate_on_submit():
            search_id = ChartRoom.query.filter_by(meeting_id=join_form.meeting_id2.data).first()
            return redirect(url_for('chat_page', room_name=search_id.meeting_name, room_id=search_id.meeting_id))

    return render_template('menu.html', form=create_form, form2=join_form, rooms=user_room, )


# logout user
@app.route("/logout-user")
def logout():
    logout_user()
    return redirect(url_for('login_page'))


# chat sections
@app.route("/chat-page/<room_name>/<room_id>")
def chat_page(room_name, room_id):
    return render_template("chat_room.html", user_room=room_name, rooms_id=room_id)


@socketio.on("incoming")
def message_handler(data):
    send(data, room=data["room"])


# user joining a room
@socketio.on("join")
def join_handler(data):
    join_room(data['room'])
    emit("user_msg", {"msg": f"{data['username']}   joined the room", "username": data["username"]}, room=data["room"])


if __name__ == "__main__":
    app.run()
