import os
import sys
import json
import datetime

from sqlalchemy import Text, DateTime, Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

engine = create_engine('sqlite:///game.db', encoding='utf8')
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

    def create_session(self, user_ip):
        new_session = UserSession(user=self, ip=user_ip)
        session.add(new_session)
        session.commit()
        return new_session

    def active_session(self):
        session.query(UserSession).filter(UserSession.user == self, UserSession.active == True)

    def kick(self):
        pass
               

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
    team = Column(Integer)
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
        self.user.level = user_name
        session.commit()

    def set_user_level(self, user_level):
        self.user.name = user_level
        session.commit()

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
    
    def set_team(self, team):
        self.team = team
        session.commit()

    def disconnect(self):
        self.is_active = False
        self.disconnected_at = datetime.datetime.utcnow()
        session.commit()

    def change_team(self, side):
        self.set_player_variable("PlayerAlliance", 0 if self.team == 1 else 1)

    def force_deck(self, deck_string):
        self.set_player_variable("PlayerDeckContent", deck_string)

    def set_player_variable(self, variable_name, variable_value):
        from parser import Rcon
        Rcon.execute("setpvar {} {} {}".format(self.user.user_id, variable_name, variable_value)) 

    def kick(self):
        from parser import Rcon
        self.is_kicked = True
        session.commit()
        Rcon.execute("kick {}".format(self.user.user_id))

    def ban(self):
        from parser import Rcon
        self.is_banned = True
        self.user.is_banned = True
        session.commit()
        Rcon.execute("ban {}".format(self.user.user_id))


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
        session.commit()
        return new_session

    def mark_leaver(self, user_session):
        existing = session.query(UserGame).filter(
            UserGame.user==user_session.user, 
            UserGame.game_session==self
        ).all()
        if existing:
            existing[0].leaver = True
            session.commit()

    def create_user_games(self, user_sessions):
        user_games = []
        for user_session in user_sessions:
            user_games += [UserGame(
                game_session=self,
                user=user_session.user,
                team=user_session.team
            )]
        session.bulk_save_objects(user_games)
        session.commit()

    def set_settings(self, settings_update):
        for key in settings_update:
            self.settings_blob[key] = settings_update[key]
        self.settings = json.dumps(self.settings_blob)
        session.commit()


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
    leaver = Column(Boolean, unique=False, default=False)


Base.metadata.create_all(engine)

def get_user(eugen_id):
    print eugen_id
    existing = session.query(User).filter(User.eugen_id==int(eugen_id)).all()
    if existing:
        return existing[0]
    else:
        print "creating new"
        new_user = User(eugen_id=int(eugen_id))
        session.add(new_user)
        session.commit()
        return new_user