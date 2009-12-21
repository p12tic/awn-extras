# Copyright (C) 2009  Danielle Madeley <danielle@madeley.id.au>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * The names of its contributors may not be used to endorse or promote
#   products derived from this software without specific prior written
#   permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from Queue import Queue
import sys
from threading import Thread
import traceback

import gobject


class ThreadQueue(object):

    def __init__(self):
        self.q = Queue()

        t = Thread(target=self._thread_worker)
        t.setDaemon(True)
        t.start()

    def add_request(self, func, *args, **kwargs):
        """Add a request to the queue. Pass callback= and/or error= as
           keyword arguments to receive return from functions or exceptions.

        """
        self.q.put((func, args, kwargs))

    def _thread_worker(self):
        while True:
            request = self.q.get()
            self.do_request(request)
            self.q.task_done()

    def do_request(self, (func, args, kwargs)):
        if 'callback' in kwargs:
            callback = kwargs['callback']
            del kwargs['callback']
        else:
            callback = None

        if 'error' in kwargs:
            error = kwargs['error']
            del kwargs['error']
        else:
            error = None

        try:
            r = func(*args, **kwargs)
            if not isinstance(r, tuple):
                r = (r,)
            if callback:
                self.do_callback(callback, *r)
        except Exception, e:
            if error:
                tb = traceback.format_exception(type(e), e, sys.exc_traceback)
                self.do_callback(error, *(e, tb))
            else:
                print "Unhandled error:", e

    def do_callback(self, callback, *args):
        def _callback(callback, args):
            callback(*args)
            return False
        gobject.idle_add(_callback, callback, args)


def async_method(func):
    """Makes the given method asynchronous, meaning when it is called it
       will be queued with add_request.

    """
    def bound_func(obj, *args, **kwargs):
        obj.add_request(func, obj, *args, **kwargs)

    return bound_func

