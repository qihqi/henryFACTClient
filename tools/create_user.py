from hashlib import sha1
import sys
from coreapi import dbapi
from henry.users.dao import User

def main():
    username = sys.argv[1]
    password = sys.argv[2]

    user = User()
    user.username = username
    s = sha1()
    s.update(password.encode('utf-8'))
    user.password = s.hexdigest()
    user.level = 3
    user.is_staff = True
    user.last_factura = 0
    user.bodega_factura_id = 1
    with dbapi.session:
        dbapi.create(user)

if __name__ == '__main__':
    main()
