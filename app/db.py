import os
import sys
import json
import yaml
import datetime

from sqlalchemy import Text, DateTime, Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine, desc

from config import CONFIG

engine = create_engine(CONFIG["database"])
engine.raw_connection().connection.text_factory = unicode
Base = declarative_base()
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


class User(Base):
    __tablename__ = 'user'
    __table_args__ = {'sqlite_autoincrement': True}
    id = Column(Integer, primary_key=True, autoincrement=True)
    eugen_id = Column(Integer, nullable=False)
    name = Column(String(250))
    level = Column(Integer)
    is_banned = Column(Boolean, default=False)
    unbanned_at = Column(DateTime)

    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)

    def game_count(self):
        return len(session.query(UserGame).filter(UserGame.user==self).all())

    def session_count(self):
        return len(session.query(UserSession).filter(UserSession.user==self).all())

    def leaver_count(self):
        return len(session.query(UserGame).filter(UserGame.user==self, UserGame.is_leaver==True).all())

    def create_session(self, user_ip):
        new_session = UserSession(user=self, ip=user_ip)
        session.add(new_session)
        session.commit()
        return new_session

    def active_session(self):
        res = session.query(UserSession).filter(UserSession.user == self, UserSession.is_active == True).all()
        if res:
            return res[0]
        else:
            return None

class Deck(Base):
    __tablename__ = 'deck'
    __table_args__ = {'sqlite_autoincrement': True}
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    deck_string = Column(Text)
    battlegroup = Column(String(250))
    deck_type = Column(String(250))
    faction = Column(String(250))
    def __init__(self, *args, **kwargs):
        super(Deck, self).__init__(*args, **kwargs)
        deck_info = self.parse_deck_string(kwargs["deck_string"])
        self.battlegroup = deck_info["battlegroup"]
        self.deck_type = deck_info["type"]
        self.faction = deck_info["faction"]

    def parse_deck_string(self, deck_string):
        deck_list = {
            "Cc": {"battlegroup": "3rd Armored", "type": "Armored", "faction": "Allied"},
            "DM": {"battlegroup": "4th Armored", "type": "Armored", "faction": "Allied"},
            "CU": {"battlegroup": "101st Airborne", "type": "Airborne", "faction": "Allied"},
            "CY": {"battlegroup": "2nd Infantry", "type": "Infantry", "faction": "Allied"},
            "Bc": {"battlegroup": "2e Blindee", "type": "Armored", "faction": "Allied"},
            "C8": {"battlegroup": "Demi-Brigade SAS", "type": "Airborne", "faction": "Allied"},
            "DI": {"battlegroup": "7th Armored", "type": "Armored", "faction": "Allied"},
            "CQ": {"battlegroup": "Guards Armored", "type": "Armored", "faction": "Allied"},
            "CM": {"battlegroup": "6th Airborne", "type": "Airborne", "faction": "Allied"},
            "CI": {"battlegroup": "15th Infantry", "type": "Infantry", "faction": "Allied"},
            "Cs": {"battlegroup": "1st SSB", "type": "Infantry", "faction": "Allied"},
            "BY": {"battlegroup": "3rd Canadian Infantry", "type": "Mechanized", "faction": "Allied"},
            "CE": {"battlegroup": "1 Pancerna", "type": "Armored", "faction": "Allied"},
            "CA": {"battlegroup": "Panzer-Lehr", "type": "Armored", "faction": "Axis"},
            "Bk": {"battlegroup": "12. SS-Panzer", "type": "Armored", "faction": "Axis"},
            "DA": {"battlegroup": "2. Panzer", "type": "Armored", "faction": "Axis"},
            "C4": {"battlegroup": "9. Panzer", "type": "Armored", "faction": "Axis"},
            "Bs": {"battlegroup": "21. Panzer", "type": "Armored", "faction": "Axis"},
            "Bg": {"battlegroup": "116. Panzer", "type": "Armored", "faction": "Axis"},
            "Bo": {"battlegroup": "17. SS-Panzergrenadier", "type": "Mechanized", "faction": "Axis"},
            "B0": {"battlegroup": "3. Fallschirmjager", "type": "Airborne", "faction": "Axis"},
            "C0": {"battlegroup": "16. Luftwaffe", "type": "Infantry", "faction": "Axis"},
            "B8": {"battlegroup": "91. Luftlande", "type": "Infantry", "faction": "Axis"},
            "DE": {"battlegroup": "Festung Gros-Paris", "type": "Infantry", "faction": "Axis"},
            "Bw": {"battlegroup": "352. Infanterie", "type": "Infantry", "faction": "Axis"},
            "B4": {"battlegroup": "P716. Infanterie", "type": "Infantry", "faction": "Axis"}
        }
        prefix = deck_string[1:3]
        if prefix in deck_list:
            return deck_list[prefix]
        else:
            return {"battlegroup": "Unknown", "type": "Unknown", "Infantry": "Unknown"}

class UserSession(Base):
    __tablename__ = 'user_session'
    __table_args__ = {'sqlite_autoincrement': True}
    id = Column(Integer, primary_key=True, autoincrement=True)
    is_active = Column(Boolean, unique=False, default=True)
    is_kicked = Column(Boolean, unique=False, default=False)
    is_banned = Column(Boolean, unique=False, default=False)
    ip = Column(String(250))
    team = Column(Integer, default=0)
    connected_at = Column(DateTime)
    disconnected_at = Column(DateTime)
    deck_id = Column(Integer, ForeignKey('deck.id'))
    deck = relationship(Deck)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    def __init__(self, *args, **kwargs):
        super(UserSession, self).__init__(*args, **kwargs)
        self.connected_at = datetime.datetime.utcnow()

    def set_user_name(self, user_name):
        self.user.name = user_name
        session.commit()

    def set_user_level(self, user_level):
        self.user.level = user_level
        session.commit()

    def summary(self):
        return {
            "name": self.user.name,
            "level": self.user.level,
            "eugen_id": self.user.eugen_id,
            "game_count": self.user.game_count(),
            "session_count": self.user.session_count(),
            "leaver_count": self.user.leaver_count(),
            "connected_time": format_timedelta(self.connected_time()),
            "battlegroup": self.deck.battlegroup
        }

    def set_deck(self, deck_string):
        existing = session.query(Deck).filter(
            Deck.user==self.user, 
            Deck.deck_string==deck_string
        ).all()
        if existing:
            self.deck = existing[0]
        else:
            new_deck = Deck(
                user=self.user, 
                deck_string=deck_string
            )
            session.add(new_deck)
            self.deck = new_deck
        session.commit()

    def connected_time(self):
        return datetime.datetime.utcnow() - self.connected_at
    
    def set_team(self, team):
        self.team = team
        session.commit()

    def disconnect(self):
        self.is_active = False
        self.disconnected_at = datetime.datetime.utcnow()
        session.commit()

    def swap(self):
        self.set_player_variable("PlayerAlliance", 0 if self.team == 1 else 1)

    def force_deck(self, deck_string):
        self.set_player_variable("PlayerDeckContent", deck_string)

    def set_player_variable(self, variable_name, variable_value):
        from parser import Rcon
        Rcon.execute("setpvar {} {} {}".format(self.user.eugen_id, variable_name, variable_value)) 

    def kick(self):
        from parser import Rcon
        self.is_kicked = True
        session.commit()
        Rcon.execute("kick {}".format(self.user.eugen_id))

    def ban(self):
        from parser import Rcon
        self.is_banned = True
        self.user.is_banned = True
        session.commit()
        Rcon.execute("ban {}".format(self.user.eugen_id))


class GameSession(Base):
    __tablename__ = 'game_session'
    __table_args__ = {'sqlite_autoincrement': True}
    id = Column(Integer, primary_key=True, autoincrement=True)
    game_state = Column(String(250), default="lobby")
    lobby_start_at = Column(DateTime)
    game_start_at = Column(DateTime)
    game_end_at = Column(DateTime)
    active = Column(Boolean, unique=False, default=True)
    settings = Column(Text)

    def __init__(self, *args, **kwargs):
        super(GameSession, self).__init__(*args, **kwargs)
        self.lobby_start_at = datetime.datetime.utcnow()
        self.settings_blob = {}
        self.settings = json.dumps(self.settings_blob)

    def __str__(self):
        return "id: {}, active: {}, game_state: {}, lobby_time: {}, game_time: {}, leaver_count: {}".format(
            self.id,
            self.active,
            self.game_state, 
            self.lobby_time(),
            self.game_time(),
            self.leaver_count()
        )
    
    def summary(self):
        return {
            "id": self.id,
            "game_state": self.game_state,
            "lobby_start_at": str(self.lobby_start_at),
            "lobby_time": format_timedelta(self.lobby_time()),
            "game_start_at": str(self.game_start_at),
            "game_time": format_timedelta(self.game_time()),
            "game_end_at": str(self.game_end_at),
            "active": self.active,
            "settings": json.loads(self.settings)
        }

    def lobby_time(self):
        if self.game_start_at:
            return self.game_start_at - self.lobby_start_at
        else:
            return datetime.datetime.utcnow() - self.lobby_start_at

    def game_time(self):
        if self.game_state == "running":
            return datetime.datetime.utcnow() - self.game_start_at
        elif self.game_state == "complete":
            return self.game_end_at - self.game_start_at
        else:
            return datetime.timedelta()

    def leaver_count(self):
        return len(session.query(UserGame).filter(UserGame.game==self, UserGame.is_leaver==True).all())

    def push_initial_settings(self, settings_blob):
        self.settings_blob = settings_blob
        self.settings = json.dumps(self.settings_blob)

    def start_game(self, user_sessions):
        self.game_state = "running"
        self.game_start_at = datetime.datetime.utcnow()
        self.create_user_games([user_sessions[key] for key in user_sessions])
        session.commit()

    def end_game(self):
        self.game_state = "complete"
        self.game_end_at = datetime.datetime.utcnow()
        session.commit()

    def new_session(self):
        self.active = False
        new_session = GameSession()
        new_session.push_initial_settings(self.settings_blob)
        session.add(new_session)
        session.commit()
        return new_session

    def mark_leaver(self, user_session):
        existing = session.query(UserGame).filter(
            UserGame.user==user_session.user, 
            UserGame.game_session==self
        ).all()
        if existing:
            existing[0].is_leaver = True
            session.commit()

    def create_user_games(self, user_sessions):
        print "creating User Games for {} users".format(len(user_sessions))
        for user_session in user_sessions:
            session.add(UserGame(
                game_session=self,
                user=user_session.user,
                team=user_session.team
            ))
            session.commit()

    def set_settings(self, settings_update):
        for key in settings_update:
            self.settings_blob[key] = settings_update[key]
        self.settings = json.dumps(self.settings_blob)
        session.commit()

    def set_server_setting(self, variable_name, variable_value):
        from parser import Rcon
        Rcon.execute("setsvar {} {}".format(variable_name, variable_value)) 


class UserGame(Base):
    __tablename__ = 'user_game'
    __table_args__ = {'sqlite_autoincrement': True}
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    deck_id = Column(Integer, ForeignKey('deck.id'))
    deck = relationship(Deck)
    game_session_id = Column(Integer, ForeignKey('game_session.id'))
    game_session = relationship(GameSession)
    team = Column(Integer)
    is_leaver = Column(Boolean, unique=False, default=False)


Base.metadata.create_all(engine)

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
    return '%s:%02d:%02d' % (hours, minutes, seconds)

def first_game_session():
    first_session = GameSession()
    session.add(first_session)
    session.commit()
    return first_session

def current_game_session():
    return session.query(GameSession).order_by(desc(GameSession.id)).limit(1).all()[0]

def get_user(eugen_id):
    existing = session.query(User).filter(User.eugen_id==int(eugen_id)).all()
    if existing:
        return existing[0]
    else:
        new_user = User(eugen_id=int(eugen_id))
        session.add(new_user)
        session.commit()
        return new_user