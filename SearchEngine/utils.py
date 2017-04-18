# coding: utf-8
import os
import sys
from functools import wraps

import time
from multiprocessing import Pool, Manager, cpu_count


MSG_START = "[START]"
MSG_SUCCESS = "[SUCCESS]"
MSG_FAILED = "[FAILED]"


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

    percents = str_format.format(100 * (iteration / float(total)) if not total == 0 else 100)
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


def log_prof_data(logger):
    logger.debug("Profiling data:")
    for fname, data in PROF_DATA.items():
        max_time = max(data[1])
        avg_time = sum(data[1]) / len(data[1])
        logger.debug("Function %s: %d calls, %.3fs max time, %.3fs avg time", fname, data[0], max_time, avg_time)
        clear_prof_data()


def print_prof_data():
    print("Function run times:")
    d = []
    for fname, data in PROF_DATA.items():
        max_time = max(data[1])
        total_time = sum(data[1])
        avg_time = total_time / len(data[1])
        d.append((fname, data[0], max_time, avg_time, total_time))

    d = sorted(d, key=lambda x: x[4], reverse=True)

    for _d in d:
        # print("%s\n\t%d calls\n\t%.3fs max time\n\t%.3fs avg time\n\t%.3fs total time" % _d)
        print("%s\t%.3fs total time" % (_d[0], _d[4]))
        clear_prof_data()


def clear_prof_data():
    # Function copied from http://stackoverflow.com/questions/3620943/measuring-elapsed-time-with-the-time-module
    global PROF_DATA
    PROF_DATA = {}


def get_files(directory, extension=None):
    """ Returns a list of absolute paths of the files in dir and its subdirectories. """

    _files = []
    for subdir, dirs, files in os.walk(directory):
        for file in files:
            name, _extension = os.path.splitext(file)
            file_path_abs = os.path.normpath(os.path.join(subdir, file))
            if extension is None or _extension == extension:
                _files.append(file_path_abs)
    return _files


def process_batch(args_list, fn, process_no=cpu_count()):
    total_iterable = len(args_list)

    p = Pool(process_no)
    m = Manager()
    q = m.Queue()

    args = [(fn, q, args) for args in args_list]

    results = p.map_async(batch_handler, args)
    while (True):
        # Print progress
        i = q.qsize()
        print_progress(i, total_iterable, 'Progress:')

        if results.ready():
            break
        time.sleep(0.2)

    result = results.get()
    p.close()
    p.join()
    return result


def batch_handler(args):
    fn, q, fn_args = args
    result = fn(*fn_args)
    q.put(True)
    return result


def check_python_version():
    python_version = sys.version_info

    if python_version[0] < 3:
        print('Must use python 3, you are currently using {}.{}'.format(python_version[0], python_version[1]))
        exit()
