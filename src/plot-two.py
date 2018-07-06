#!/usr/bin/env python3
# Requires matplotlib; pip install matplotlib
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
import matplotlib; matplotlib.use('Agg')  # noqa; for systems without X11
from matplotlib.backends.backend_pdf import PdfPages
import pylab as plt
import logging as log

from lib.parsev3bw import v3bw_fd_into_xy

log.basicConfig(level=log.INFO)


def _get_data(inputs):
    '''
    Takes a list of (fname, label) pairs.

    Returns a dictionary like {
        'label1': {
            'AAAA': 40,
            'BBBB': 90,
        },
        'label2': {
            'AAAA': 30,
            'BBBB': 80,
        },
    }
    '''
    data = {}
    for fname, label in inputs:
        assert label not in data, 'Already have input file with label '\
            '%s' % label
        data[label] = {}
        with open(fname, 'rt') as fd:
            for fp, bw in v3bw_fd_into_xy(fd):
                if fp in data[label]:
                    log.warning('Already saw fp %s in %s. Overwriting',
                                fp[0:8], label)
                data[label][fp] = bw
        log.info('Read %s for %s', len(data[label]), label)
    return data


def _to_points(data, xkey=None):
    '''
    Takes the dictionary from _get_data()

    Returns a dictionary like {
        'AAAA': (40, 30),
        'BBBB': (90, 80),
    }

    If xkey is specified, then that label will be used for the X value in the
    points. Otherwise an arbitrary label will be chosen.
    '''
    points = {}
    assert len(data.keys()) == 2, 'Only can have two input files'
    xkey = xkey or [k for k in data.keys()][0]
    ykey = [key for key in data.keys() if key != xkey][0]
    for fp in data[xkey]:
        if fp not in data[ykey]:
            continue
        assert fp not in points
        points[fp] = (data[xkey][fp], data[ykey][fp])
    log.info('%s and %s share %s fingerprints', xkey, ykey, len(points))
    return points


def _plot_against_45deg(args, pdf, points):
    xkey = args.input[0][1]
    ykey = args.input[1][1]
    x, y = zip(*[points[fp] for fp in points])
    plt.figure()
    plt.scatter(x, y, s=args.size)
    plt.xlabel('Bandwidth according to %s (KB)' % xkey)
    plt.ylabel('Bandwidth according to %s (KB)' % ykey)
    plt.xlim(xmin=0)
    plt.ylim(ymin=0)
    if args.xmax_45deg is not None:
        plt.xlim(xmax=args.xmax_45deg)
    if args.ymax_45deg is not None:
        plt.ylim(ymax=args.ymax_45deg)
    title = 'How closely %s and %s match' % (xkey, ykey)
    plt.title(title)
    log.info(
        'Plotting "%s". Each point is a relay with results from both %s '
        'and %s. The X values of the points come from %s and the Y '
        'values come from %s', title, xkey, ykey, xkey, ykey)
    log.info('The more that the dots hug the 45 degree line, the more similar '
             '%s and %s are. If the dots are mostly above the line, %s '
             'generally measured relays faster. If the dots are mostly below '
             'the line, %s generally measured them faster.',
             xkey, ykey, ykey, xkey)
    plt.plot(range(0, int(args.xmax_45deg or 1000000)), c='gray')
    pdf.savefig()


def _plot_sorted_curves_impl(args, pdf, data, sort_key):
    '''
    Takes the dictionary from _get_data()
    '''
    plt.figure()
    other_key = [k for k in data.keys() if k != sort_key]
    assert len(other_key) == 1
    other_key = other_key[0]
    title = 'Relays sorted by bandwidth according to %s' % sort_key
    log.info('Plotting "%s"', title)
    log.info(
        'Each relay has a given X value based on how fast %s thinks it is. '
        'On that X value, the relay has two points: one of each color. '
        'If %s\'s data seems to be somewhat of a trend line for %s\'s '
        'data, then the two are pretty similar.',
        sort_key, sort_key, other_key)
    fps = set()
    for fp in data[sort_key]:
        if fp in data[other_key]:
            fps.add(fp)
    yvalue_pairs = []
    for fp in fps:
        sort_key_bw = data[sort_key][fp]
        other_key_bw = data[other_key][fp]
        yvalue_pairs.append((sort_key_bw, other_key_bw))
    yvalue_pairs = sorted(yvalue_pairs, key=lambda item: item[0], reverse=True)
    sort_key_line, other_key_line = zip(*yvalue_pairs)
    plt.scatter(range(len(fps)), sort_key_line, s=args.size, label=sort_key)
    plt.scatter(range(len(fps)), other_key_line, s=args.size, label=other_key)
    plt.xlim(xmin=0)
    plt.ylim(ymin=0)
    if args.ymax_sorted_curve:
        plt.ylim(ymax=args.ymax_sorted_curve)
    plt.title(title)
    plt.legend(loc='upper right')
    plt.xlabel('Arbitrary relay number (lower is faster)')
    plt.ylabel('Bandwidth (KB)')
    pdf.savefig()


def _plot_sorted_curves(args, pdf, data):
    for key in data.keys():
        _plot_sorted_curves_impl(args, pdf, data, key)


def main(args, pdf):
    xkey = args.input[0][1]
    data = _get_data(args.input)
    points = _to_points(data, xkey=xkey)
    _plot_against_45deg(args, pdf, points)
    _plot_sorted_curves(args, pdf, data)


if __name__ == '__main__':
    d = 'Takes two v3bw files and plots useful graphs with the data '\
        'contained within.'
    parser = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter, description=d)
    parser.add_argument(
        '-i', '--input', nargs=2, metavar=('FNAME', 'LABEL'),
        action='append', help='Specify a file to read values from and what '
        'to label its points in the PDF. Must be given exactly twice.')
    parser.add_argument(
        '--xmax-45deg', type=float, default=None,
        help='Maximum X value on graph with 45 degree gray line')
    parser.add_argument(
        '--ymax-45deg', type=float, default=None,
        help='Maximum Y value on graph with 45 degree gray line')
    parser.add_argument('-o', '--output', default='temp.pdf')
    parser.add_argument('-s', '--size', type=float, default=1,
                        help='Size of scatter plot points')
    parser.add_argument(
        '--ymax-sorted-curve', type=float, default=None,
        help='Maximum Y value on graphs with 2 scatter plots sorted by one '
        'input\'s values')

    args = parser.parse_args()
    if args.input is None or len(args.input) != 2:
        print('Two input files must be given. Try --help')
        exit(1)
    with PdfPages(args.output) as pdf:
        exit(main(args, pdf))
