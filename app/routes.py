from app import app
from collections import defaultdict
from flask import render_template, jsonify, send_from_directory
from db import session, current_game_session, UserSession, User

@app.route('/')
def index():
    active_users = session.query(User).all()
    return send_from_directory('static', 'html/index.html')

@app.route('/game/state')
def game_state():
    return jsonify(current_game_session().summary())

@app.route('/users/current')
def users_current():
    session.commit()
    active_sessions = session.query(UserSession).filter(UserSession.is_active==True).all()
    allied_users = [x.summary() for x in active_sessions if x.team == 0]
    axis_users = [x.summary() for x in active_sessions if x.team == 1]
    session.commit()
    return jsonify({"axis_users": axis_users, "allied_users": allied_users})

@app.route('/users/kick/<eugen_id>')
def users_kick(eugen_id):
    session.commit()
    user = find_user(eugen_id)
    if not user:
        return jsonify({"success": False, "message": "could not find active session"})
    active_session = user.active_session()
    if active_session:
        active_session.kick()
        session.commit()
        return jsonify({"success": True, "message": "kicked {}".format(user.name)})
    else:
        return jsonify({"success": False, "message": "could not find active session"})

@app.route('/users/ban/<eugen_id>')
def users_ban(eugen_id):
    session.commit()
    user = find_user(eugen_id)
    if not user:
        return jsonify({"success": False, "message": "could not find active session"})
    active_session = user.active_session()
    if active_session:
        active_session.ban()
        session.commit()
        return jsonify({"success": True, "message": "banned {}".format(user.name)})
    else:
        return jsonify({"success": False, "message": "could not find active session"})

@app.route('/users/swap/<eugen_id>')
def users_swap(eugen_id):
    session.commit()
    user = find_user(eugen_id)
    if not user:
        return jsonify({"success": False, "message": "could not find active session"})
    active_session = user.active_session()
    if active_session:
        active_session.swap()
        session.commit()
        return jsonify({"success": True, "message": "swapped {}".format(user.name)})
    else:
        return jsonify({"success": False, "message": "could not find active session"})

def find_user(eugen_id):
    session.commit()
    res = session.query(User).filter(User.eugen_id==eugen_id).all()
    session.commit()
    if res:
        return res[0]
    else:
        return None
