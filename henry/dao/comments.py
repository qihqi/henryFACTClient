import os
import uuid
from henry.base.dbapi import DBApi, dbmix
from henry.schema.meta import NComment, NImage, NTodo

# from PIL import Image as PilImage
PilImage = None
Comment = dbmix(NComment)
Image = dbmix(NImage)
Todo = dbmix(NTodo)


class ImageServer:
    def __init__(self, imgbasepath, imgapi, fileapi):
        self.imgbasepath = imgbasepath
        self.imgapi = imgapi
        self.fileapi = fileapi

    def getimg(self, objtype, objid):
        imgs = self.imgapi.search(objtype=objtype, objid=objid)

        def addpath(img):
            _, imgfile = os.path.split(img.path)
            img.imgurl = os.path.join(self.imgbasepath, imgfile)
            return img

        return map(addpath, imgs)

    def saveimg(self, objtype, objid, data):
        _, ext = os.path.splitext(data.raw_filename)
        filename = uuid.uuid1().hex + ext
        filename = self.fileapi.make_fullpath(filename)
        im = PilImage.open(data.file)
        if im.size[0] > 1024:
            im.resize((1024, 768))
        im.save(filename)
        img = Image(
            objtype=objtype, objid=objid,
            path=filename)
        self.imgapi.create(img)
        return img

