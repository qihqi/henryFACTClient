from sqlalchemy.inspection import inspect

def decode_str(strobj):
    try:
        return strobj.decode('utf8')
    except:
        return strobj.decode('latin1')


def mkgetter(obj):
    if hasattr(obj, 'get'):
        return obj.get
    return obj.__getattribute__


def mksetter(obj):
    if hasattr(obj, 'get'):
        return obj.__setitem__
    return obj.__setattr__


def fieldcopy(src, dest, fields):
    srcgetter = mkgetter(src)
    destsetter = mksetter(dest)
    for f in fields:
        try:
            value = srcgetter(f)
            if isinstance(value, str):
                value = decode_str(value)
            destsetter(f, value)
        except:
            pass


# A method that converts a class of SQLAlchemy model into
# a serializeble object
# APIs:
#     .db_instance() returns an object of the given class with the same data
#     .serialize() returns an dict with same data
#     Class.from_db_instance, and Class.deserialize do the opposite
def dbmix(database_class, override_name=()):
    class DataObjectMixin(object):
        db_class = database_class
        _columns = inspect(database_class).columns
        pkey = inspect(database_class).primary_key[0]

        def __init__(self, **kwargs):
            self.merge_from(kwargs)

        def db_instance(self):
            result = self.db_class()
            fieldcopy(self, result, self._columns.keys())
            return result

        @classmethod
        def from_db_instance(cls, db_instance):
            y = cls()
            fieldcopy(db_instance, y, cls._columns.keys())
            return y

        def merge_from(self, obj):
            fieldcopy(obj, self, self._columns.keys())
            return self

        def serialize(self):
            return self._serialize_helper(self, self._columns.keys())

        @classmethod
        def deserialize(cls, dict_input):
            result = cls().merge_from(dict_input)
            for x, y in override_name:
                original = dict_input.get(y, None)
                setattr(result, x, original)
            return result

        @classmethod
        def _serialize_helper(cls, obj, names):
            result = {}
            fieldcopy(obj, result, names)
            for x, y in override_name:
                original = result[x]
                result[y] = original
                del result[x]
            return result
    return DataObjectMixin


class DBApi(object):

    def __init__(self, sessionmanager, objclass):
        self.sm = sessionmanager
        self.objclass = objclass
        self.api = DBApiGeneric(sessionmanager)

    def create(self, obj):
        return self.api.create(obj)

    def get(self, pkey):
        return self.api.get(pkey, self.objclass)

    def update(self, pkey, content_dict):
        obj = self.objclass()
        setattr(obj, self.objclass.pkey.name, pkey)
        return self.api.update(obj, content_dict)

    def delete(self, pkey):
        obj = self.objclass()
        setattr(obj, self.objclass.pkey.name, pkey)
        return self.api.delete(obj)

    def getone(self, **kwargs):
        return self.api.getone(self.objclass, **kwargs)

    def search(self, **kwargs):
        return self.api.search(self.objclass, **kwargs)


class DBApiGeneric(object):

    def __init__(self, sessionmanager):
        self.sm = sessionmanager

    @property
    def session(self):
        return self.sm

    @property
    def db_session(self):
        return self.sm.session

    def create(self, obj):
        dbobj = obj.db_instance()
        self.sm.session.add(dbobj)
        self.sm.session.flush()
        pkey = obj.pkey.name
        pkeyval = getattr(dbobj, pkey)
        setattr(obj, pkey, pkeyval)
        return pkeyval

    def get(self, pkey, objclass):
        db_instance = self.sm.session.query(objclass.db_class).filter(
            objclass.pkey == pkey).first()
        if db_instance is None:
            return None
        return objclass.from_db_instance(db_instance)

    def update(self, obj, content_dict):
        pkey = getattr(obj, obj.pkey.name)
        count = self.sm.session.query(obj.db_class).filter(
            obj.pkey == pkey).update(
            content_dict)
        obj.merge_from(content_dict)
        return count

    def delete(self, obj):
        pkey = getattr(obj, obj.pkey.name)
        count = self.sm.session.query(obj.db_class).filter(
            obj.pkey == pkey).delete()
        return count

    def getone(self, objclass, **kwargs):
        result = self.search(objclass, **kwargs)
        if not result:
            return None
        return result[0]

    def search(self, objclass, **kwargs):
        query = self.sm.session.query(objclass.db_class)
        for key, value in kwargs.items():
            mode = None
            if '-' in key:
                key, mode = key.split('-')
            col = objclass._columns[key]
            f = col == value
            if mode == 'prefix':
                f = col.startswith(value)
            if mode == 'lte':
                f = col <= value
            if mode == 'gte':
                f = col >= value
            query = query.filter(f)
        return map(objclass.from_db_instance, iter(query))
