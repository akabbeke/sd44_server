from app import app
from collections import defaultdict
from flask import render_template, jsonify, send_from_directory
from db import session, UserSession, User

@app.route('/')
def index():
    active_users = session.query(User).all()
    return send_from_directory('templates', 'index.html')

@app.route('/users/current')
def users_current():
    session.commit()
    active_sessions = session.query(UserSession).filter(UserSession.is_active==True).all()
    allied_users = [session_summary(x) for x in active_sessions if x.team == 0]
    axis_users = [session_summary(x) for x in active_sessions if x.team == 1]
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

def format_timedelta(delta):
    s = delta.seconds
    # hours
    hours = s // 3600 
    # remaining seconds
    s = s - (hours * 3600)
    # minutes
    minutes = s // 60
    # remaining seconds
    seconds = s - (minutes * 60)
    # total time
    return '%s:%s:%s' % (hours, minutes, seconds)

def session_summary(user_session):
    return {
        "name": user_session.user.name,
        "level": user_session.user.level,
        "eugen_id": user_session.user.eugen_id,
        "game_count": user_session.user.game_count(),
        "session_count": user_session.user.session_count(),
        "leaver_count": user_session.user.leaver_count(),
        "connected_time": format_timedelta(user_session.connected_time()),
        "battlegroup": user_session.deck.battlegroup
    }
