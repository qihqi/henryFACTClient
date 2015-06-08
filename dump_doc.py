import sys

from henry.config import transapi
from henry.base.serialization import json_dump


def main():
    x = sys.argv[1]
    print json_dump(transapi.get_doc(x))

if __name__ == '__main__':
    main()
