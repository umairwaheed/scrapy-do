#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   26.11.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import importlib
import os

from twisted.internet.protocol import ProcessProtocol
from twisted.internet.defer import Deferred
from twisted.internet import reactor, task
from distutils.spawn import find_executable
from datetime import datetime
from schedule import Job as SchJob


#-------------------------------------------------------------------------------
def exc_repr(e):
    """
    Return a string representation of an exception together with the excepion
    name.
    """
    return "{}: {}".format(type(e).__name__, str(e))


#-------------------------------------------------------------------------------
def get_object(name):
    """
    Retrieve an object from a module given its fully qualified name. For
    example: `get_object('scrapy_do.webservice.Status')`
    """
    name = name.split('.')
    object_name = name[-1]
    module = importlib.import_module('.'.join(name[:-1]))
    return getattr(module, object_name)


#-------------------------------------------------------------------------------
class TimeStamper:
    """
    Set the timestamp attribute of the object whenever the associated attribute
    is set. For example:

    :Example:

        >>> class Test:
        >>>     attr = TimeStamper('_attr')
        >>>
        >>>     def __init__(self, attr):
        >>>         self._attr = attr
        >>>         self.timestamp = datetime.now()
        >>> test = Test('foo')
        >>> test.attr
        'foo'
        >>> test.timestamp
        datetime.datetime(2017, 12, 2, 23, 0, 56, 671634)
        >>> test.attr = 'bar'
        >>> test.timestamp
        datetime.datetime(2017, 12, 2, 23, 1, 9, 688899)
    """

    #---------------------------------------------------------------------------
    def __init__(self, attr_name):
        self.attr_name = attr_name

    #---------------------------------------------------------------------------
    def __get__(self, obj, obj_type):
        return getattr(obj, self.attr_name)

    #---------------------------------------------------------------------------
    def __set__(self, obj, value):
        obj.timestamp = datetime.now()
        return setattr(obj, self.attr_name, value)


#-------------------------------------------------------------------------------
def _build_directive_map(job):
    #---------------------------------------------------------------------------
    # A list of valid directives
    #---------------------------------------------------------------------------
    directive_names = ['second', 'seconds', 'minute', 'minutes', 'hour',
                       'hours', 'day', 'days', 'week', 'weeks', 'monday',
                       'tuesday', 'wednesday', 'thursday', 'friday',
                       'saturday', 'sunday', 'at', 'to']

    #---------------------------------------------------------------------------
    # Get an appropriate setter reference
    #---------------------------------------------------------------------------
    def get_attr(obj, attr):
        for obj in [obj] + obj.__class__.mro():
            if attr in obj.__dict__:
                ret = obj.__dict__[attr]
                if isinstance(ret, property):
                    return lambda x: ret.__get__(x, type(x))
                return ret

    #---------------------------------------------------------------------------
    # Build the dictionary of setters
    #---------------------------------------------------------------------------
    directive_map = {}
    for d in directive_names:
        directive_map[d] = get_attr(job, d)

    return directive_map


#-------------------------------------------------------------------------------
def _parse_args(directive, directives):
    #---------------------------------------------------------------------------
    # Check the argument to "to"
    #---------------------------------------------------------------------------
    if directive == 'to':
        arg = directives.pop()
        try:
            arg = int(arg)
        except ValueError:
            raise ValueError('The "to" directive expects an integer')
        return [arg]

    #---------------------------------------------------------------------------
    # Check the argument to "at"
    #---------------------------------------------------------------------------
    if directive == 'at':
        arg = directives.pop()
        arg_split = arg.split(':')

        if len(arg_split) != 2:
            raise ValueError('The "at" directive expects a string like "12:34"')

        try:
            int(arg_split[0])
            int(arg_split[1])
        except ValueError:
            raise ValueError('The "at" directive expects a string like "12:34"')

        return [arg]

    #---------------------------------------------------------------------------
    # Nothing else accepts arguments
    #---------------------------------------------------------------------------
    return []


#-------------------------------------------------------------------------------
def _parse_spec(job, spec):
    #---------------------------------------------------------------------------
    # Check the directive
    #---------------------------------------------------------------------------
    directives = spec.lower().split()

    if len(directives) < 2:
        raise ValueError('Spec too short')

    if directives[0] != 'every':
        raise ValueError('Spec must start with "every"')

    #---------------------------------------------------------------------------
    # Set up the interval if necessary
    #---------------------------------------------------------------------------
    try:
        interval = int(directives[1])
        job.interval = interval

        if len(directives) < 3:
            raise ValueError("Spec to short")
        directives = directives[2:]
    except ValueError:
        directives = directives[1:]

    #---------------------------------------------------------------------------
    # Parse the spec
    #---------------------------------------------------------------------------
    directive_map = _build_directive_map(job)
    directives.reverse()
    while directives:
        directive = directives.pop()
        if directive not in directive_map:
            raise ValueError('Unknown directive: ' + directive)

        args = _parse_args(directive, directives)

        try:
            directive_map[directive](job, *args)
        except AssertionError as e:
            raise ValueError(str(e))

    return job


#-------------------------------------------------------------------------------
def schedule_job(scheduler, spec):
    job = SchJob(1, scheduler)
    try:
        _parse_spec(job, spec)
    except Exception:
        scheduler.cancel_job(job)
        raise
    return job


#-------------------------------------------------------------------------------
def arg_require_all(dict, args):
    for arg in args:
        if arg not in dict:
            raise KeyError('Missing argument "{}"'.format(arg))


#-------------------------------------------------------------------------------
def arg_require_any(dict, args):
    for arg in args:
        if arg in dict:
            return
    raise KeyError('Neither argument present: "{}"'.format(str(args)))


#-------------------------------------------------------------------------------
def twisted_sleep(time):
    return task.deferLater(reactor, time, lambda: None)


#-------------------------------------------------------------------------------
class LoggedProcessProtocol(ProcessProtocol):

    #---------------------------------------------------------------------------
    def __init__(self, job_name, log_dir):
        self.finished = Deferred()
        self.out_path = os.path.join(log_dir, job_name + '.out')
        self.err_path = os.path.join(log_dir, job_name + '.err')
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        self.out_fd = os.open(self.out_path, flags, 0o644)
        self.err_fd = os.open(self.err_path, flags, 0o644)
        os.set_inheritable(self.out_fd, True)
        os.set_inheritable(self.err_fd, True)

    #---------------------------------------------------------------------------
    def processExited(self, status):
        out_size = os.fstat(self.out_fd).st_size
        err_size = os.fstat(self.err_fd).st_size
        os.close(self.out_fd)
        os.close(self.err_fd)
        if out_size == 0:
            os.remove(self.out_path)
        if err_size == 0:
            os.remove(self.err_path)

        self.finished.callback(status.value.exitCode)


#-------------------------------------------------------------------------------
def run_process(cmd, args, job_name, log_dir, env=None, path=None):
    cmd = find_executable(cmd)
    args = [cmd] + args
    pp = LoggedProcessProtocol(job_name, log_dir)
    p = reactor.spawnProcess(pp, cmd, args, env=env, path=path,
                             childFDs={1: pp.out_fd, 2: pp.err_fd})
    return p, pp.finished


#-------------------------------------------------------------------------------
def pprint_relativedelta(delta):
    ret = ''
    if delta.years:
        ret += '{}y '.format(delta.years)
    if delta.days:
        ret += '{}d '.format(delta.days)
    if delta.hours:
        ret += '{}h '.format(delta.hours)
    if delta.minutes:
        ret += '{}m '.format(delta.minutes)
    ret += '{}s'.format(delta.seconds)
    return ret
