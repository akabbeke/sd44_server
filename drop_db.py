from app.db import User, UserSession, Deck, GameSession, UserGame

try:
    UserGame.__table__.drop()
except:
    pass

try:
    GameSession.__table__.drop()
except:
    pass

try:
    UserSession.__table__.drop()
except:
    pass

try:
    Deck.__table__.drop()
except:
    pass

try:
    User.__table__.drop()
except:
    pass