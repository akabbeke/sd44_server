import sys
print sys.path
sys.path.insert(0, '/var/www/html/flaskapp/')
from app import app as application
