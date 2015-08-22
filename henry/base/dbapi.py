from sqlalchemy.inspection import inspect

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
            destsetter(f, value)
        except:
            pass

def dbmix(database_class):
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

        def serialize(self):
            return self._serialize_helper(self, self._columns.keys())

        @classmethod
        def deserialize(cls, dict_input):
            return cls().merge_from(dict_input)

        @classmethod
        def _serialize_helper(cls, obj, names):
            return {
                name: getattr(obj, name) for name in names if getattr(obj, name, None) is not None
            }
    return DataObjectMixin


class DBApi(object):

    def __init__(self, sessionmanager, objclass):
        self.sm = sessionmanager
        self.objclass = objclass

    def create(self, obj):
        dbobj = obj.db_instance()
        self.sm.add(dbobj)

    def get(self, pkey):
        db_instance = self.sm.session.query(self.objclass.db_class).filter(
            self.objclass.pkey == pkey).first()
        return self.objclass.from_db_instance(db_instance)

    def update(self, pkey, content_dict):
        count = self.sm.session.query(self.objclass.db_class).filter(
            self.objclass.pkey == pkey).update(
            content_dict)
        return count

    def delete(self, pkey):
        count = self.sm.session.query(self.objclass.db_class).filter(
            self.objclass.primary_key == pkey).delete()
        return count

    def search(self, **kwargs):
        query = self.sm.session.query(self.objclass.db_class)
        for key, value in kwargs.items():
            mode = None
            if '-' in key:
                key, mode = key.split('-')
            f = self.objclass._columns[key] == value
            if mode == 'prefix':
                f = self.objclass._columns[key].startswith(value)
            query = query.filter(f)
        return map(self.objclass.from_db_instance, query)
