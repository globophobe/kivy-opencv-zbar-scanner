import datetime
from kivy.clock import Clock


class UTCMixin(object):
    def get_utc(self):
        return datetime.datetime.now(datetime.timezone.utc)


class NetworkRetryMixin(object):
    def get_elapsed_time(self, utc):
        elapsed_time = datetime.datetime.now(datetime.timezone.utc) - utc
        return elapsed_time.total_seconds()

    def retry_on_error(
        self, callback, request_init, max_time=1000, retry_interval=250, error=None
    ):
        assert max_time > 0
        assert retry_interval > 0
        elapsed_time = self.get_elapsed_time(request_init)
        milliseconds = elapsed_time * 1000
        if milliseconds <= max_time:
            # Try again in 100 milliseconds
            Clock.schedule_once(callback, retry_interval / 1000)
        else:
            if callable(error):
                error()
