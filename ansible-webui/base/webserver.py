from multiprocessing import cpu_count
from string import ascii_letters
from random import choice as random_choice

import gunicorn
from gunicorn.app.wsgiapp import WSGIApplication

from aw.config.hardcoded import PORT_WEB
from aw.utils.deployment import deployment_dev, warn_if_development

# https://docs.gunicorn.org/en/stable/settings.html
OPTIONS_DEV = {
    'reload': True,
    'loglevel': 'info',
    'workers': 2,
}
OPTIONS_PROD = {
    'bind': f'127.0.0.1:{PORT_WEB}',
    'reload': False,
    'loglevel': 'warning',
}


class StandaloneApplication(WSGIApplication):
    def __init__(self, app_uri, options=None):
        self.options = options or {}
        self.app_uri = app_uri
        super().__init__()

    def load_config(self):
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)


def create_webserver() -> WSGIApplication:
    gunicorn.SERVER = ''.join(random_choice(ascii_letters) for _ in range(10))
    run_options = {
        'workers': (cpu_count() * 2) + 1,
        **OPTIONS_PROD
    }
    if deployment_dev():
        warn_if_development()
        run_options = {**run_options, **OPTIONS_DEV}

    return StandaloneApplication(
        app_uri="aw.main:app",
        options=run_options
    )
