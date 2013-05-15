import gc
import inspect
import json
import logging
import os
import psutil
import sys
import time
import thread
import traceback

from collections import defaultdict
from threading import Thread

from sys import _current_frames

log = logging.getLogger('memprof')

ONE_MB = 1024 * 1024
ONE_GB = 1024 * ONE_MB


class RecurringTimer(Thread):
    def __init__(self, tick, target, args=None, kwargs=None):
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}

        self.tick = tick
        self.target = target
        self.args = args
        self.kwargs = kwargs
        self.stopped = False

        Thread.__init__(self)

    def run(self):
        while not self.stopped:
            self.target(*self.args, **self.kwargs)
            time.sleep(self.tick)


def get_thread_frame(thread_id):
    return _current_frames()[thread_id]


def watch_thread(output, threshold=ONE_GB, tick=5.0, abort_on_hit=False):
    t = RecurringTimer(
        10, memcheck, kwargs={
            'output': output,
            'threshold': threshold,
            'abort_on_hit': abort_on_hit,
            'parent_thread_id': thread.get_ident(),
        },
    )
    t.daemon = True
    t.start()


def with_class(objs):
    for o in objs:
        if not hasattr(o, '__class__'):
            continue
        yield o


def dump_memory(filename, frame):
    if not frame:
        frame = inspect.currentframe()

    with open(filename, 'wb') as fp:
        process = psutil.Process(os.getpid())
        mem_info = process.get_ext_memory_info()

        fp.write(json.dumps({
            'stack': traceback.format_stack(frame),
            'cmd': process.cmdline,
            'openfiles': [
                dict(
                    (k, getattr(f, k))
                    for k in ('path', 'fd')
                )
                for f in process.get_open_files()
            ],
            'mem': dict(
                (k, getattr(mem_info, k))
                for k in ('rss', 'vms')
            ),
        }) + '\n')

        for obj in with_class(gc.get_objects()):
            refs_by_type = defaultdict(int)
            # for ref in with_class(gc.get_referents(obj)):
            #     refs_by_type[str(type(ref))] += 1
            fp.write(json.dumps({
                'id': id(obj),
                'class': str(type(obj)),
                'size': sys.getsizeof(obj, 0),
                'value_trim': repr(obj)[:100],
                'referents': dict(refs_by_type),
            }) + '\n')


def memcheck(output, threshold=ONE_GB, abort_on_hit=False,
             parent_thread_id=None):
    if not parent_thread_id:
        parent_thread_id = thread.get_ident()

    pid = os.getpid()
    rss = psutil.Process(pid).get_memory_info().rss
    sys.stderr.write('Process {} rss={}MB (threshold={}MB)'.format(
        pid, rss / ONE_MB, threshold / ONE_MB))

    if rss > threshold:
        filename = os.path.join(
            output, 'memorydump-{0}.json'.format(int(time.time())))
        frame = get_thread_frame(parent_thread_id)

        sys.stderr.write(
            'TRESHOLD EXCEEDED: dumping profile to {} (this make take a while)\n'.format(
                filename))

        try:
            dump_memory(filename, frame)
        finally:
            if abort_on_hit:
                sys.stderr.write('Aboring execution due to memory threshold\n')
                os.abort()


def analyze(filename):
    results_by_type = defaultdict(lambda: {
        'num': 0,
        'examples': defaultdict(int),
        'size': 0,
    })
    with open(filename) as fp:
        header = json.loads(fp.readline())
        for line in fp:
            result = json.loads(line)
            tp = results_by_type[result['class']]
            tp['num'] += 1
            tp['size'] += result['size']
            tp['examples'][result['value_trim']] += 1

    results_by_type = sorted(
        results_by_type.items(),
        key=lambda x: x[1]['size'],
        reverse=True)

    tmpl = '%-50s %-10s %-10s'
    print tmpl % ('Type', 'Count', 'Size')
    print '-' * 80
    for cls_name, result in results_by_type[:50]:
        print tmpl % (cls_name, result['num'], result['size'])
        examples = sorted(result['examples'].items(), key=lambda x: x[1], reverse=True)
        for name, count in examples[0:1]:
            print '-> (%s) %s' % (count, name)

if __name__ == '__main__':
    filename = sys.argv[1]
    analyze(filename)
