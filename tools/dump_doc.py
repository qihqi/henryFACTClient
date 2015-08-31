import sys

from henry.config import transapi
from henry.base.serialization import json_dumps


def main():
    x = sys.argv[1]
    print json_dumps(transapi.get_doc(x))

if __name__ == '__main__':
    main()
