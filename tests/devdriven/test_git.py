from pathlib import Path
from os import system
from devdriven.util import cwd
from devdriven.git import GitLog, GitDiff, rev_parse, git_repo_url

TMP_DIR = "/tmp/devdriven-python/test/test_git"

def test_git_repo_url():
  url = 'https://github.com/ORG/REPO/PATH'
  assert git_repo_url(url) == url
  assert git_repo_url('git@github.com:ORG/REPO.git') == 'https://github.com/ORG/REPO'

def test_commits_between():
  base_dir = TMP_DIR
  git_log = GitLog(base_dir)
  (id1, id2) = commit_ids()

  commits_1 = git_log.commits_between(id1, id2)
  commits_1_refs = {c.ref for c in commits_1}
  assert len(commits_1) == 3

  commits_2 = git_log.commits_between(id2, id1)
  commits_2_refs = {c.ref for c in commits_2}
  assert len(commits_2) == 3
  assert [c.to_dict() for c in commits_1] == [c.to_dict() for c in commits_2]
  assert (commits_1[0].to_dict().keys() == {
          'ref', 'timestamp', 'committer_email', 'directory', 'subject'
          })
  ref_1 = rev_parse(TMP_DIR, 'commit_1')[0]
  ref_2 = rev_parse(TMP_DIR, 'commit_2')[0]
  ref_3 = rev_parse(TMP_DIR, 'commit_3')[0]
  _ref_4 = rev_parse(TMP_DIR, 'commit_4')[0]
  expected_refs = {
    ref_1,
    ref_2,
    ref_3,
  }
  assert commits_1_refs == expected_refs
  assert commits_2_refs == expected_refs

def test_files_changed():
  base_dir = TMP_DIR
  (id1, id2) = commit_ids()
  expected_files = [
    'a.txt',
    'b.txt',
  ]
  assert GitDiff(base_dir).files_changed(id1, id2) == expected_files
  assert GitDiff(base_dir).files_changed(id2, id1) == expected_files

def commit_ids():
  return ('commit_1', 'commit_3')

def setup_module():
  base_dir = TMP_DIR
  Path(base_dir).mkdir(parents=True, exist_ok=True)
  with cwd(base_dir):
    commands = '''
rm -rf .git *.txt
ls -la
git init

touch a.txt
git add .
git commit -m 'commit_1'
git tag commit_1

touch b.txt
git add .
git commit -m 'commit_2'
git tag commit_2

echo "commit_3" > a.txt
git add .
git commit -m 'commit_3'
git tag commit_3

echo "commit_4" > c.txt
git add .
git commit -m 'commit_4'
git tag commit_4

ls -la
git ls-files
git log -p
git tag --list
git rev-parse --verify commit_1
git rev-parse --verify commit_2
git rev-parse --verify commit_3
git rev-parse --verify commit_4
    '''
    return [run(cmd) for cmd in commands.splitlines()]

def teardown_module():
  print("teardown_module")

def run(cmd):
  system(f'exec 2>&1; set -e; cd "{TMP_DIR}"; set -x; ' + cmd)
