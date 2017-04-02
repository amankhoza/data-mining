import sys
from functools import wraps

import logging

logger = logging.getLogger(__name__)

import time


def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, bar_length=100):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        bar_length  - Optional  : character length of bar (Int)
    """
    # This function was copied from https://gist.github.com/aubricus/f91fb55dc6ba5557fbab06119420dd6a

    str_format = "{0:." + str(decimals) + "f}"
    percents = str_format.format(100 * (iteration / float(total)))
    filled_length = int(round(bar_length * iteration / float(total)))
    bar = '█' * filled_length + '-' * (bar_length - filled_length)

    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix)),

    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()


def print_progress(iteration, total, prefix='', suffix='', decimals=1):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        bar_length  - Optional  : character length of bar (Int)
    """
    str_format = "{0:." + str(decimals) + "f}"
    percents = str_format.format(100 * (iteration / float(total)))
    progress = '%d / %d' % (iteration, total)

    sys.stdout.write('\r%s %s (%s%s) %s' % (prefix, progress, percents, '%', suffix)),

    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()


PROF_DATA = {}


def profile(fn):
    # Function copied from http://stackoverflow.com/questions/3620943/measuring-elapsed-time-with-the-time-module
    @wraps(fn)
    def with_profiling(*args, **kwargs):
        start_time = time.time()

        ret = fn(*args, **kwargs)

        elapsed_time = time.time() - start_time

        if fn.__name__ not in PROF_DATA:
            PROF_DATA[fn.__name__] = [0, []]
        PROF_DATA[fn.__name__][0] += 1
        PROF_DATA[fn.__name__][1].append(elapsed_time)

        return ret

    return with_profiling


def log_prof_data():
    logger.info("Profiling data:")
    for fname, data in PROF_DATA.items():
        max_time = max(data[1])
        avg_time = sum(data[1]) / len(data[1])
        logger.debug("Function %s: %d calls, %.3f max time, %.3f avg time", fname, data[0], max_time, avg_time)
        clear_prof_data()


def clear_prof_data():
    # Function copied from http://stackoverflow.com/questions/3620943/measuring-elapsed-time-with-the-time-module
    global PROF_DATA
    PROF_DATA = {}


MSG_START = "[START]"
MSG_SUCCESS = "[SUCCESS]"
MSG_FAILED = "[FAILED]"