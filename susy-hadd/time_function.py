import resource
import os

DEBUG=os.environ.get('DEBUG', False)


def time_function(name):
    def _time_function(function):
        def __time_function(*args, **kwargs):
            usage_start = resource.getrusage(resource.RUSAGE_CHILDREN)
            result = function(*args, **kwargs)
            usage_end = resource.getrusage(resource.RUSAGE_CHILDREN)

            cpu_time = usage_end.ru_utime - usage_start.ru_utime
            # RSS = https://en.wikipedia.org/wiki/Resident_set_size
            memory = usage_end.ru_maxrss / 1024.  # now in MB
            msg = "Ran '{name}' in {cpu_time:.1f}s and used {memory:.1f}MB of RAM"
            msg = msg.format(name=name, cpu_time=cpu_time, memory=memory)
            if DEBUG: print(msg)
            return result
        return __time_function
    return _time_function
