from devdriven.config import Config
from icecream import ic

def test_config():
  conf = Config(file_default='tests/devdriven/data/config.yml').load()
