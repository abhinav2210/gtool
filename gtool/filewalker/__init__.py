import patricia as pt
import gtool.namespace
import os

# --- static ---
__DYNAMIC_CLASS = 'filematches'

def filematcher():
    return __DYNAMIC_CLASS

# a shared globals ala...
# http://stackoverflow.com/questions/15959534/python-visibility-of-global-variables-in-imported-modules

def registerFileMatcher(fileExp, classObj):
    if fileExp in globals()[filematcher()]:
        # this error will occur for a misconfig or a security event
        raise KeyError('One class tried to overwrite the file registration of an existing one. Class name: %s' % classObj)
    else:
        globals()[filematcher()][fileExp] = classObj
        return True

def filematchspace():
    return globals()[filematcher()]

def filematch(exp):
    T = globals()[filematcher()]
    try:
        #print('file match:', T.key(exp), 'has a value of', T[T.key(exp)])
        return gtool.namespace.namespace()[T[T.key(exp)]]
    except KeyError:
        return None

#--- classes ---


class StructureFactory(object):

    class Inode(object):
        def __init__(self, nodepath=None, nodename=None, parent=None):
            if nodepath is not None:
                rootdir = nodepath.rstrip(os.sep)
                # print('nodepath:', rootdir)
                self.path = nodepath
            else:
                self.path = None

            self.__nodename__ = nodename
            if isinstance(parent, StructureFactory.Directory):
                self.__parent__ = parent
                self.__parent__.addchild(self)
            else:
                self.__parent__ = None
            self.__children__ = []

        @property
        def parent(self):
            return self.__parent__

        @property
        def name(self):
            return self.__nodename__

        def addparent(self, parent):
            self.__parent__ = parent

        def __repr__(self):
            if self.parent is None:
                return '%s' % (self.__nodename__)
            else:
                return '%s\\%s' % (self.__parent__.__repr__(), self.__nodename__)

        def __str__(self):
            return '%s' % self.__nodename__

    class File(Inode):

        def read(self):
            if self.path is None:
                raise AttributeError('The file path was not provided when the File object was created')
            with open(self.path, mode='r') as f:
                _ret = f.readlines()
                f.close()
            return _ret


    class Directory(Inode):

        def __init__(self, nodename=None, parent=None, nodepath=None):
            super().__init__(nodename=nodename, parent=parent, nodepath=nodepath)
            self.__children__ = []

        @property
        def children(self):
            return self.__children__

        def addchild(self, child):
            self.__children__.append(child)
            child.addparent(self)

        def __repr__(self):
            if self.parent is None:
                return '%s' % (self.__nodename__)
            else:
                return '%s\\%s' % (self.__parent__.__repr__(), self.__nodename__)

        def __str__(self):
            return '%s' % self.__nodename__

        def tree(self):
            # print(self.__str__())
            for child in self.children:
                print(child.__repr__())
                if isinstance(child, StructureFactory.Directory):
                    child.tree()

    class Node(object):

        def __init__(self, name=None, fileobject=None, parent=None):
            # TODO consolidate fileobjects and children
            self.__name__ = name
            self.__inode__ = fileobject
            self.__parent__ = parent
            self.__children__ = []

        def addchildren(self, node):
            if isinstance(node, list):
                for _node in node:
                    self.__children__.append(_node)
                    _node.__parent__ = self
            else:
                self.__children__.append(node)
                node.__parent__ = self

        @property
        def fileobject(self):
            return self.__inode__

        @property
        def path(self):
            if self.__inode__ is not None:
                return self.__inode__.path
            else:
                return None

        @property
        def children(self):
            return self.__children__

        @property
        def name(self):
            return self.__name__

        def __str__(self):
            # TODO return number of children and type (file or dir)
            return self.__name__

        def __repr__(self):
            return '%s: %s' % (type(self), self.__name__)

        @property
        def uri(self):
            if self.__parent__ is not None:
                return  "%s\%s" % (self.__parent__.uri, self.__name__)
            else:
                return "%s" % self.__name__

        @property
        def __objectmatch__(self):
            _ret = filematch(self.name)
            if _ret is None:
                raise KeyError('%s at %s does not match any known class definition' % (self.name, self.path))
            return _ret

        @property
        def __data__(self):
            if isinstance(self.__inode__, StructureFactory.File):
                return ''.join(self.__inode__.read())
            else:
                raise TypeError('%s is not a file' % self.__inode__.path)

        @property
        def dataasobject(self):
            _retobject = self.__objectmatch__()
            #print(_retobject)
            if _retobject.loads(self.__data__): # True if loadstring works
                return _retobject
            else:
                raise TypeError('Could not parse the data from %s into a %s class' % (self.path, type(_retobject)))


    class Container(Node):

        """
        An inherited class for the purposes of type differentiaton and overriding the data methods
        """

        @property
        def __data__(self):
            return '%s' % self.__name__

    class CNode(Node):

        """
        An inherited class for the purposes of type differentiaton and overriding the data methods
        """

        @property
        def __data__(self):
            """
            returns a string of the root node data but not of any attributes that are dynamic classes
            :return: str
            """
            _ret = str()
            _filelist = [f for f in self.fileobject.children if isinstance(f, StructureFactory.File)]
            _coredata = [f.data for f in _filelist if f.name is "_.txt"]
            if len(_coredata) == 1:
                _ret += ''.join(_coredata[0].read())
            else:
                raise FileNotFoundError('In %s the _.txt file was expected' % self.fileobject.path)

            for _file in (f for f in _filelist if f.name is not "_.txt"):
                _data = ''.join(_file.read())
                if '@' not in _data[0]:
                    _ret += '@%s' % _file.name
                    _ret += _data

            for subdir in (f for f in self.fileobject.children if isinstance(f, StructureFactory.Directory)):
                subfilelist = [subfile for subfile in subdir.children]
                if '_.txt' not in (subfile.name for subfile in subfilelist):
                    for subfile in subfilelist:
                        _ret += '@%s' % subfile.name
                        _ret += subfile.read()

            print('return data:', _ret)
            return _ret

        @property
        def dataasobject(self):
            _retobject = self.__objectmatch__()
            # print(_retobject)
            _softload = True
            if not _retobject.loads(self.__data__, softload=_softload):  # True if loadstring works
                raise TypeError('Could not parse the data from %s into a %s class' % (self.path, type(_retobject)))
            if len(_retobject.missingproperties) == 0:
                return _retobject

            _filelist = [f for f in self.fileobject.children if isinstance(f, StructureFactory.File)]
            for _file in (f for f in _filelist if f.name is not "_.txt"):
                _data = ''.join(_file.read())
                if '@' in _data[0]:
                    _attrobj = StructureFactory.Node(name=_file.name, fileobject=_file)
                    _retobject[_file.name] = _attrobj.dataasobject
                    if _file.name in _retobject.missingproperties:
                        _retobject.__missing_dynamic_properties__.remove(_file.name)
                    else:
                        raise TypeError('Got an attribute file %s that is not part of the %s class at %s' %
                                         (_file.name, self.name, self.path))

            for subdir in (f for f in self.fileobject.children if isinstance(f, StructureFactory.Directory)):
                subfilelist = [subfile for subfile in subdir.children]
                if '_.txt' in (subfile.name for subfile in subfilelist):
                    for subfile in subfilelist:
                        _attrobj = StructureFactory.CNode(name=subfile.name, fileobject=subfile)
                        _retobject[subfile.name] = _attrobj.dataasobject
                    if subfile.name in _retobject.missingproperties:
                        _retobject.__missing_dynamic_properties__.remove(subfile.name)
                    else:
                        raise TypeError('Got an attribute directory %s that is not part of the %s class at %s' %
                                        (subfile.name, type(_retobject), self.path))

            if len(_retobject.missingproperties) > 0:
                raise TypeError('The following mandatory attributes are missing %s for the %s class at %s' %
                                (_retobject.missingproperties, type(_retobject), self.path))

            return _retobject


    @staticmethod
    def __treewalk__(root):
        inodes = os.listdir(root.path)
        for inode in inodes:
            fullpath = os.path.join(root.path, inode)
            if os.path.isfile(fullpath):
                _f = StructureFactory.File(nodename=inode, nodepath=fullpath)  # parent=root,
                root.addchild(_f)
            elif os.path.isdir(fullpath):
                _d = StructureFactory.Directory(nodename=inode, nodepath=fullpath)  # , parent=root
                root.addchild(_d)
                StructureFactory.__treewalk__(_d)

    @staticmethod
    def __walk__(location=None):

        def recursivewalk(location=None, isroot=False):
            #TODO deal with multiple files in a dir and multiple dirs at the root
            if isinstance(location, StructureFactory.Directory):
                if '_.txt' in [f.name for f in location.children]:
                    print('Node Container:', location.name)
                    return StructureFactory.CNode(fileobject=location, name=location.name)
                else:
                    # special handler for root of structure
                    _locationname = location.name if isroot is False else '*'
                    print('Container:', _locationname)
                    _ret = StructureFactory.Container(name=_locationname, fileobject=location)
                    for child in location.children:
                        _ret.addchildren(recursivewalk(child))
                    return _ret
            elif isinstance(location, StructureFactory.File):
                _rootname = location.name.split('.')[0]
                print('Node:', _rootname)
                return StructureFactory.Node(fileobject=location, name=_rootname)

        if not isinstance(location, StructureFactory.Directory):
            raise TypeError('start of file system must be a directory')
        #ret = StructureFactory.Node2(name='*')
        #ret.addchildren(recursivewalk(location=location, isroot=True))
        return recursivewalk(location=location, isroot=True)

    # TODO make this the init call for the class so it can return a new node object with all data (more pythonic)
    @staticmethod
    def treewalk(rootpath):
        # TODO check this is a valid directory before proceeding
        rootdir = rootpath.rstrip(os.sep)
        rootobj = StructureFactory.Directory(nodename=rootdir, nodepath=rootpath)
        StructureFactory.__treewalk__(rootobj) # TODO make this return an actual object
        return StructureFactory.__walk__(location=rootobj)

#--- initialize namespace
globals()[filematcher()] = pt.trie('_')
