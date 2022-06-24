from enum import Enum
from requests.exceptions import MissingSchema
import re
from requests.models import PreparedRequest


class Stream(Enum):
    audio = 1
    video = 2


yt_regex_str = '^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$'

yt_regex = re.compile(yt_regex_str)


def check_url(url):
    prepared_request = PreparedRequest()
    try:
        prepared_request.prepare_url(url, None)
        return prepared_request.url
    except MissingSchema as e:
        return False
