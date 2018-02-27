import re
import os
import yaml

from time import sleep
from subprocess import call
from random import random
from math import floor

from config import CONFIG
from db import session, first_game_session, User, UserSession, UserGame, GameSession, Deck, get_user
from rcon import MCRcon


class Rcon:
    @classmethod
    def execute(cls, command):
        
        client = MCRcon()
        client.connect(
            CONFIG["rcon"]["ip"], 
            CONFIG["rcon"]["port"],
            CONFIG["rcon"]["password"]
        )
        return client.command(command)


class Game:
    """Main class, containing game process manipulation"""

    # -------------------------------------------
    # User event handlers
    # -------------------------------------------

    def on_player_connect(self, playerid):
        pass

    def on_player_deck_set(self, playerid, playerdeck):
        pass

    def on_player_level_set(self, playerid, playerlevel):
        pass

    def on_player_elo_set(self, playerid, playerelo):
        pass

    def on_player_side_change(self, playerid, playerside):
        pass

    def on_player_name_change(self, playerid, playername):
        pass

    def on_player_disconnect(self, playerid):
        pass

    def on_switch_to_game(self):
        pass

    def on_switch_to_debriefing(self):
        pass

    def on_switch_to_lobby(self):
        pass

    def on_set_variable(self, variable_name, variable_value):
        pass

    # -------------------------------------------
    # Custom actions
    # -------------------------------------------

    # Forcing certain deck usage
    def assign_decks(self):

        general_blue_deck = "XuAVOOkCbkxlBEyoMkgTf1Il1KtJYkaaQ9JaVnSbFS0syQUqwUlT/FVELI6A1nLhNYKTUsil9ScaLGLg"
        general_red_deck = "tOAcF6LTLwXEYZMocldI1qnDBZdjgqZZZKW4aUMuHEbSSRMWR2SyIWytaL9KelYE/A=="

        for playerID, player in self.players.items():
            if player.get_side() == Side.Bluefor:
                if player.get_deck() != general_blue_deck:
                    player.change_deck(general_blue_deck)

            if player.get_side() == Side.Redfor:
                if player.get_deck() != general_red_deck:
                    player.change_deck(general_red_deck)

    def map_random_rotate(self):
        """Rotate maps from the pool"""
        map_pool = [
            "_3x2_Colombelles",
            "_5x2_10v10_Pegaville",
        ]

        self.game_session.set_server_setting("Map", random.choice(map_pool))

    def limit_level(self, playerid, playerlevel):
        """Kick players below certain level"""
        limit = 7
        if playerlevel < limit:
            print("Player level is too low: " + str(playerlevel) + ". Min is " + str(limit) + ". Kicking...")
            self.players[playerid].kick()


# ----------------------------------------------------------------------------------------------------------------------
# --------------------------------------- INTERNAL IMPLEMENTATION DETAILS ----------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

    # -------------------------------------------
    # Service event handlers
    # -------------------------------------------

    def _on_player_connect(self, match_obj):

        eugen_id = match_obj.group(1)
        user_ip = match_obj.group(4)

        user = get_user(eugen_id)

        # Creating player data structure if not present
        if not (eugen_id in self.user_instances):
            self.user_instances[eugen_id] = user.create_session(user_ip)

        if not self.first_run:
            self.on_player_connect(eugen_id)

    # ----------------------------------------------
    def _on_player_deck_set(self, match_obj):

        eugen_id = match_obj.group(1)
        deck_string = match_obj.group(2)

        self.user_instances[eugen_id].set_deck(deck_string)

        if not self.first_run:
            self.on_player_deck_set(eugen_id, deck_string)

    # ----------------------------------------------
    def _on_player_level_set(self, match_obj):

        eugen_id = match_obj.group(1)
        user_level = match_obj.group(2)

        self.user_instances[eugen_id].set_user_level(int(user_level))

        if not self.first_run:
            self.on_player_level_set(eugen_id, int(user_level))

    # ----------------------------------------------
    def _on_player_elo_set(self, match_obj):

        eugen_id = match_obj.group(1)
        user_elo = match_obj.group(2)

        # self.players[playerid].set_elo(float(playerelo))

        if not self.first_run:
            self.on_player_elo_set(eugen_id, user_elo)

    # ----------------------------------------------
    def _on_player_disconnect(self, match_obj):

        eugen_id = match_obj.group(1)

        self.user_instances[eugen_id].disconnect()

        if self.game_session.game_state == "running":
            self.game_session.mark_leaver(self.user_instances[eugen_id])

        if not self.first_run:
            self.on_player_disconnect(eugen_id)

        del self.user_instances[eugen_id]

    # ----------------------------------------------
    def _on_player_side_change(self, match_obj):

        eugen_id = match_obj.group(1)
        team = match_obj.group(2)

        self.user_instances[eugen_id].set_team(int(team))

        if not self.first_run:
            self.on_player_side_change(eugen_id, team)

    # ----------------------------------------------
    def _on_player_name_change(self, match_obj):

        eugen_id = match_obj.group(1)
        user_name = match_obj.group(2)
        self.user_instances[eugen_id].set_user_name(user_name)

        if not self.first_run:
            self.on_player_name_change(eugen_id, user_name)

    # ----------------------------------------------
    def _on_switch_to_game(self, match_obj):

        self.game_session.start_game(self.user_instances)

        if not self.first_run:
            self.on_switch_to_game()

    # ----------------------------------------------
    def _on_switch_to_debriefing(self, match_obj):

        self.game_session.end_game()

        if not self.first_run:
            self.on_switch_to_debriefing()

    # ----------------------------------------------
    def _on_switch_to_lobby(self, match_obj):

        self.game_session = self.game_session.new_session()

        if not self.first_run:
            self.on_switch_to_lobby()

    def _on_set_variable(self, match_obj):

        variable_name = match_obj.group(1)
        variable_value = match_obj.group(2)
        self.game_session.set_settings({variable_name: variable_value})

        if not self.first_run:
            self.on_set_variable(variable_name, variable_value)

    # ---------------------------------------------
    # Event handlers registration
    # ---------------------------------------------

    def register_events(self):
        self.register_event(
            'Client added in session \(EugNetId : ([0-9]+), UserSessionId : ([0-9]+), socket : ([0-9]+), IP : (.*)\)', 
            self._on_player_connect
        )
        self.register_event('Client ([0-9]+) variable PlayerDeckContent set to "(.*)"', self._on_player_deck_set)
        self.register_event('Client ([0-9]+) variable PlayerLevel set to "(.*)"', self._on_player_level_set)
        self.register_event('Client ([0-9]+) variable PlayerElo set to "(.*)"', self._on_player_elo_set)
        self.register_event('Client ([0-9]+) variable PlayerAlliance set to "([0-9])"', self._on_player_side_change)
        self.register_event('Client ([0-9]+) variable PlayerName set to "(.*)"', self._on_player_name_change)
        self.register_event('Disconnecting client ([0-9]+)', self._on_player_disconnect)
        self.register_event('Entering in loading phase state', self._on_switch_to_game)
        self.register_event('Entering in debriephing phase state', self._on_switch_to_debriefing)
        self.register_event('Entering in matchmaking state', self._on_switch_to_lobby)
        self.register_event('Variable (.+) set to (.+)', self._on_set_variable)

    # -------------------------------------------
    # Utility functions
    # -------------------------------------------

    def __init__(self):
        self.events = {}
        self.user_instances = {}
        self.logfile_stream = open(CONFIG["log_file"], "r")
        self.first_run = True
        self.game_session = first_game_session()
        self.register_events()

        # Getting starting line
        while True:
            line = self.logfile_stream.readline()
            if not line:
                # 0 player line is not found, reseting to the start of file
                self.logfile_stream.seek(0, os.SEEK_SET)
                break

            if line == u"Variable NbPlayer set to \"0\"\n":
                # 0 player line is found, keeping this state of the stream
                break

    def __del__(self):
        self.logfile_stream.close()

    def main(self):
        print("Server control script started")
        print("Gather information run")

        self.update()

        print("Gather information run is over")
        self.infoRun = False

        print "Found {} Users".format(len(session.query(User).all()))
        print "Found {} UserSessions".format(len(session.query(UserSession).all()))
        print "Found {} UserGames".format(len(session.query(UserGame).all()))
        print "Found {} GameSessions".format(len(session.query(GameSession).all()))
        print "Found {} Decks".format(len(session.query(Deck).all()))

        print("Server control started")

        while True:
            self.update()
            sleep(0.5)

    def register_event(self, regex, handler):
        """Register event handler for a certain log entry"""
        self.events[re.compile(regex)] = handler

    def update(self):
        import string
        printable = set(string.printable)
        
        """Parse log and trigger event handler"""
        while True:
            line = self.logfile_stream.readline()
            
            if line:
                print line
                line = filter(lambda x: x in printable, line)
                # Test against event expressions
                for pair in self.events.items():
                    match = pair[0].match(line)
                    if match:
                        pair[1](match)
                        break
                active_sessions = session.query(UserSession).filter(UserSession.is_active==True).all()
                print "active_sessions: {}".format(len(active_sessions))
                session.commit()
                
            else:
                break

# Starting everything
if __name__ == '__main__':
    Game().main()