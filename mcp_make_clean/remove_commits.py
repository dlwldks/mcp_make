def commit_callback(commit, metadata):
    bad_commits = [
        "987c406c43de34c0fc0d8d9b6bfcaf4eb635dbe6",
        "f469ea9e7602ddf5158fa37133992b02464b061e"
    ]
    if commit.original_id.decode("utf-8") in bad_commits:
        commit.ignore = True

