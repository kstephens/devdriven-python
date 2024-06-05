from devdriven.config import Config
from icecream import ic

def test_config():
  config = Config(file_default='tests/devdriven/data/config.yml').load()
  ic(config)
