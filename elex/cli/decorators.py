import os
from functools import wraps
from elex.cli.utils import parse_date
from requests.exceptions import HTTPError


def require_date_argument(fn):
    """
    Decorator that checks for date argument.
    """
    @wraps(fn)
    def decorated(self):
        name = fn.__name__.replace('_', '-')
        if self.app.pargs.data_file:
            return fn(self)
        elif len(self.app.pargs.date) and self.app.pargs.date[0]:
            try:
                self.app.election.electiondate = parse_date(
                    self.app.pargs.date[0]
                )
                return fn(self)
            except ValueError:
                text = '{0} could not be recognized as a date.'
                self.app.log.error(text.format(self.app.pargs.date[0]))
                self.app.close(1)

            return fn(self)
        else:
            text = 'No election date (e.g. `elex {0} 2015-11-\
03`) or data file (e.g. `elex {0} --data-file path/to/file.json`) specified.'
            self.app.log.error(text.format(name))
            self.app.close(1)

    return decorated


def require_ap_api_key(fn):
    """
    Decorator that checks for Associated Press API key or data-file argument.
    """
    @wraps(fn)
    def decorated(self):
        try:
            return fn(self)
        except HTTPError as e:
            if e.response.status_code == 400:
                message = e.response.json().get('errorMessage')
            elif e.response.status_code == 401:
                payload = e.response.json()
                message = payload['fault']['faultstring']
                detail = payload['fault']['detail']['errorcode']
                message = '{0} ({1})'.format(message, detail)
            else:
                message = e.response.reason
            self.app.log.error('HTTP Error {0} - {1}.'.format(e.response.status_code, e.response.reason))
            self.app.log.debug('HTTP Error {0} ({1}'.format(e.response.status_code, e.response.url))
            self.app.close(1)
        except KeyError as e:
            text = 'AP_API_KEY environment variable is not set.'
            self.app.log.error(text)
            self.app.close(1)

    return decorated
