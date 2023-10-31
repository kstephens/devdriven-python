from devdriven.git import GitLog, GitDiff

def test_commits_between():
    base_dir = '.'
    git_log = GitLog(base_dir)
    (id1, id2) = commit_ids()

    commits_1 = git_log.commits_between(id1, id2)
    commits_1_refs = {c.ref for c in commits_1}
    assert len(commits_1) == 7

    commits_2 = git_log.commits_between(id2, id1)
    commits_2_refs = {c.ref for c in commits_2}
    assert len(commits_2) == 7
    assert [c.to_dict() for c in commits_1] == [c.to_dict() for c in commits_2]
    assert (commits_1[0].to_dict().keys() == {
            'ref', 'timestamp', 'committer_email', 'directory', 'subject'
            })
    expected_refs = {
    }
    assert commits_1_refs == expected_refs
    assert commits_2_refs == expected_refs

def test_files_changed():
    base_dir = '.'
    (id1, id2) = commit_ids()
    expected_files = [
    ]
    assert GitDiff(base_dir).files_changed(id1, id2) == expected_files
    assert GitDiff(base_dir).files_changed(id2, id1) == expected_files

def commit_ids():
    return ('a', 'b')
