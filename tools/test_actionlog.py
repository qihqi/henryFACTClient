import json
import sys
import requests
from urlparse import urljoin, urlsplit, urlunsplit
from henry.dao.actionlog import ActionLog
import sys
reload(sys)
sys.setdefaultencoding('utf8')

TARGET_ADDR = 'localhost:8080'

def main():
    with open(sys.argv[1]) as input_file:
        for l in input_file.readlines():
            actionlog = ActionLog.deserialize(json.loads(l))
            scheme, netloc, path, query_string, fragment = urlsplit(actionlog.url)
            url = urlunsplit((scheme, TARGET_ADDR, path, query_string, fragment))
            r = requests.request(actionlog.method, url=url, data=actionlog.body)
            if r.status_code != 200:
                print >>sys.stderr, r.status_code, actionlog.url
                print l,
            raw_input('continue..?')


if __name__ == '__main__':
    main()
