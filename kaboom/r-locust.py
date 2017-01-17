import os
import time
import subprocess

from locust import Locust, events, task, TaskSet

from apis.R import RProcess

class RcrunchClient(object):
    
    def __init__(self, host):
        self.host = host
        self.user = os.environ.get("R_TEST_USER")
        self.pw = os.environ.get("R_TEST_PW")
        if self.user is None or self.pw is None:
            raise Exception, "Must set a user and pw"
    
    def birth(self):
        self.R = RProcess.birth()
        expr = 'options(crunch.api="%s/api/", crunch.email="%s", crunch.pw="%s"); library(crunch)' % (self.host, self.user, self.pw)
        p = self.R.run(expr)
        print p

    def __getattr__(self, name):
        expr = 'source("R/%s.R")' % name
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                p = self.R.run(expr)
                print p
            except Exception as e:
                total_time = int((time.time() - start_time) * 1000)
                events.request_failure.fire(request_type="rcrunch", name=name, response_time=total_time, exception=e)
            else:
                total_time = int((time.time() - start_time) * 1000)
                events.request_success.fire(request_type="rcrunch", name=name, response_time=total_time, response_length=0)
                # In this example, I've hardcoded response_length=0. If we would
                # want the response length to be reported correctly in the
                # statistics, we would probably need to hook in at a lower level
        
        return wrapper


class RcrunchLocust(Locust):
    """
    This is the abstract Locust class which should be subclassed. It provides an R client
    that can be used to make requests via R that will be tracked in Locust's statistics.
    """
    def __init__(self, *args, **kwargs):
        super(RcrunchLocust, self).__init__(*args, **kwargs)
        self.client = RcrunchClient(self.host)


class RcrunchUser(RcrunchLocust):
    
    min_wait = 100
    max_wait = 1000
    
    class task_set(TaskSet):
        def on_start(self):
            self.client.birth()
        
        @task(1)
        class AuthenticatedThings(TaskSet):
            def on_start(self):
                self.client.login()
            
            @task
            class AuthenticatedThings(TaskSet):
                @task
                def list_datasets(self):
                    self.client.list_datasets()
                
                @task
                class Profiles(TaskSet):
                    def on_start(self):
                        self.client.load_profiles()
                    
                    @task
                    def xtab(self):
                        self.client.xtab_profiles()

        @task(0)
        def error(self):
            self.client.error()
        
        @task(0)
        def success(self):
            self.client.success()
        

        