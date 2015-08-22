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

class DataObjectMixin(object):
    db_class = None
    _columns = None
    _pkey = None

    def __init__(self, **kwargs):
        cls = self.__class__
        if cls.db_class is None:
            raise ValueError('db_class cannot be none')
        if cls._columns is None:
            cls._columns = inspect(cls.db_class).columns
        if cls._pkey is None:
            cls._columns = inspect(cls.db_class).primary_key[0]

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


class DBApi(object):

    def __init__(self, sessionmanager, objclass):
        self.sm = sessionmanager
        self.objclass = objclass

    def create(self, obj):
        dbobj = obj.db_instance()
        self.sm.add(dbobj)

    def _get_dbobj(self, pkey):
        dbobj = self.sm.session.query(self.db_class).filter(
            self.primary_key == pkey).first()
        return dbobj

    def get(self, session, pkey):
        return self.objclass.from_db_instance(self._get_dbobj(session, pkey))

    def update(self, session, pkey, content_dict):
        count = session.query(self.db_class).filter(
            self.primary_key == pkey).update(
            content_dict)
        return count

    def delete(self, session, pkey):
        count = session.query(self.db_class).filter(
            self.primary_key == pkey).delete()
        return count

    def search(self, session, **kwargs):
        query = session.query(self.db_class)
        for key, value in kwargs.items():
            mode = None
            if '-' in key:
                key, mode = key.split('-')
            f = self._columns[key] == value
            if mode == 'prefix':
                f = self._columns[key].startswith(value)
            query = query.filter(f)
        return map(self.objclass.from_db_instance, query)
