# -*- coding:gbk -*-
__author__ = 'li.shida'

'''
Framework for getting filetype-specific metadata.

Instantiate approriate class with filename.
Return object acts like a dictionary,with key-value paris for each piece or metadata.

import fileinfo
info = fileinfo.MP3FileInfo("c:\.mp3")
print "\\n".join(["s%=%s" %(k,v) for k,v in info.items])

Framework can be extended by adding classes for particular file types,
e.g.HTMLFileInfo,MPGFileInfo,DOCFileInfo.
Each class is completely responsible for parsing its files approriately

'''

import os
import sys
from UserDict import UserDict

def stripnulls(data):
    "strip white espace and nulls"
    return data.replace("\00","").strip()

class FileInfo(UserDict):
    "store file metadata"
    def __init__(self,filename=None):
        UserDict.__init__(self)
        self["name"] = filename

class MP3FileInfo(FileInfo):
    "store ID3v1.0MP3 tags"
    tagDataMap = {
        "title":(3,33,stripnulls),
        "artist":(33,63,stripnulls),
        "album":(63,93,stripnulls),
        "year":(93,97,stripnulls),
        "comment":(97,126,stripnulls),
        "genre":(127,128,ord)
    }

    def __parse(self,filename):
        "parse ID3v1.0 tags from MP3 file"
        self.clear()

        try:
            fsock = open(filename,mode='rb',buffering=0)
            try:
                fsock.seek(-128,2)
                tagdata = fsock.read(128)
            finally:
                fsock.close()
            if tagdata[:3] == "TAG":
                for tag,(start,end,parseFunc) in self.tagDataMap.items():
                    self[tag] = parseFunc(tagdata[start:end])
        except IOError:
            pass

    def __setitem__(self, key, item):
        if key == "name" and item:
            self.__parse(item)
        FileInfo.__setitem__(self,key,item)


def listDirectory(directory,fileExtList):
    "get list of file info object for filer of particular extensions"

    fileList1 = [os.path.normcase(f) for f in os.listdir(directory)]
    fileList = [
        os.path.join(directory,f)
                for f in fileList1
                    if os.path.splitext(f)[1] in fileExtList
        ]

    def getFileInfoClass(filename,module=sys.modules[FileInfo.__module__]):
        "get file info class from filename extension"
        subclass = "%sFileInfo" % os.path.splitext(filename)[1].upper()[1:]
        return hasattr(module,subclass) and getattr(module,subclass) or FileInfo

    return [getFileInfoClass(f)(f) for f in fileList]

if __name__ == '__main__':
    for info in listDirectory("C:\mp3",'[".mp3"]'):
        print "\n".join(["%s=%s" % (k,v) for k,v in info.items()])
        print

    print stripnulls.__doc__