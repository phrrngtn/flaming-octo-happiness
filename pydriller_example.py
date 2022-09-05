from pydriller import Repository
import re
import itertools
from itertools import islice
from pathlib import Path

import json

# use mailmap
mailmap_re = r"""(?P<proper_name>[^<]+)\s+<(?P<proper_email>[^>]+)>(?P<commit_name>\s+[^<]+)?\s+<(?P<commit_email>[^>]+)>"""

commits = []
# the from_commit gives us a way of 'tailing the log'
# we have to use islice because traverse_commits returns a generator

# this code is accumulating a multi-tree of changes since a particular
# commit (which we will likely obtain on the basis of some ranking (ROW_NUMBER() OVER
# (PARTITION BY repository, ts, rn_within_chunk))
for commit in islice(
    Repository(
        "/work/git-of-theseus/", from_commit="39d27630a4543b24f0110564549f8fcbe597c5eb"
    ).traverse_commits(),
    1,
    None,
):
    # use the time_t for the author_date as it is unambiguous and is trivially
    # JSON serializable.
    this_commit = dict(
        hash=commit.hash,
        author_date=commit.author_date.timestamp(),
        author_name=commit.author.name,
        author_email=commit.author.email,
    )
    this_commit["modified_files"] = list(
        [
            dict(
                change_type=m.change_type.name,
                added_lines=m.added_lines,
                deleted_lines=m.deleted_lines,
                complexity=m.complexity,
            )
            for m in commit.modified_files
        ]
    )
    commits.append(this_commit)

# The idea behind one single blob of JSON is that it will be much easier to persist to
# the database than using an ORM and we can write queries against the blob to normalize the data
# at the dataserver *if it is required to be so*

# I frequently use the quote "what we think of that database is not the database.
#  The log is the database and what we call the database is an optimized view of the log".
# So in this case, git is the database and we are dividing logical time history (the log:
# some total ordering offered to us by git) into chunks (last persisted commit to
# whatever we have)
# and combining all those commits into a single scalar *value* which we persist.
# So the regular table in the database is a logical 'log' of segments of logical time history
# which we can *chose* to unfurl to relational form if it makes it convenient for us to
# analyze. Think of it as a way of staging a group of changes to the database in a high
# performance manner (it is just a single scalar) which can then be exploded out into however
#  many records *as a single transaction at the database*

# I think that the relevant thing is that if there is some serialization of
# changes already available, that you can divide time into non-overlapping intervals and
# write the contents of that interval as a scalar and be confident that you can
# reconstruct the relational database equivalent representation of that cumulative set of
# intervals in a mechanical manner.
print(json.dumps(commits))
