from .config import Config

def test_config():
  env = {
    'TEST_C': 'from-env',
    'TEST_D': '123',
  }
  file = 'tests/devdriven/data/config.yml'
  config = Config(
    file_default=file,
    env=env,
    env_prefix='TEST_',
    converters={'d': int}
  )
  assert config.file is None
  assert config.file_default == file
  assert config.opts == {}
  assert config.conf == {}
  assert config.env == env
  assert config.file_loaded is None
  assert config.parent is None
  assert not config.cache
  config.load()
  assert config.file_loaded == file
  assert config.conf == {'a': 123, 'b': ['asdf', 456], 'c': 78, 'd': "90"}
  assert not config.cache
  assert config.opt('a') == 123
  assert config.cache == {'a': 123}
  assert config.opt('b') == ['asdf', 456]
  assert config.opt('c') == 'from-env'
  assert config.opt('d') == 123
  assert config.get_opt('UNKNOWN') is None
  config.load()
  assert not config.cache
  assert config.opt('a', converter=str) == "123"
  assert config.opt('a') == "123"
  assert config.cache == {'a': '123'}
