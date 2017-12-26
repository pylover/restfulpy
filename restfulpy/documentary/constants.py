import re


URL_PARAMETER_PATTERN = re.compile('/(?P<key>\w+):\s?(?P<value>\w+)')
CONTENT_TYPE_PATTERN = re.compile('(\w+/\w+)(?:;\s?charset=(.+))?')
