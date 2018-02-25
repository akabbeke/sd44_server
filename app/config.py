import yaml
import os

config_file = os.path.join(os.path.dirname(__file__), "config/config.yml")
with open(config_file, 'r') as stream:
    CONFIG = yaml.load(stream)