import re


def v3bw_fd_into_xy(fd):
    '''
    Takes a file descriptor to a v3bw file as the only argument.

    Returns a generator yielding (fingerprint, bandwidth) pairs.

    Looks for lines that contain actual data. That means most of them, since
    most of them contain "node_id=" and those are the ones that are
    interesting.

    Extracts the fingerprint and bandwidth values for each of those lines and
    put them on stdout, one per line. Effectively, after ignoring other lines,
    this:
        'node_id=$AAAA...AAAA bw=12345'
    becomes this:
        ('AAAA...AAAA', 12345)

    With v1.1.0 of the v3bw file format, we no longer know if node_id or bw is
    first in the line. Hence two regular expresions and searching for the
    matched item that has 40 chars (the fingerprint)
    '''
    re1 = re.compile('.*node_id=\$?([\w]+).* bw=([\d]+).*')  # noqa
    re2 = re.compile('.*bw=([\d]+).* node_id=\$?([\w]+)')  # noqa
    for line in fd:
        if 'node_id' not in line:
            continue
        match = re1.match(line) or re2.match(line)
        if not match:
            continue
        items = match.groups()
        assert len(items) == 2
        if len(items[0]) == 40:
            yield (items[0], int(items[1]))
        else:
            yield (items[1], int(items[0]))
