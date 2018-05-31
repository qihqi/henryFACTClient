import sys
from coreapi import dbapi
from henry.importation.dao import generate_custom_for_purchase


def main():
    with dbapi.session:
        generate_custom_for_purchase(dbapi, int(sys.argv[1]))

main()
