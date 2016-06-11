from copy import copy
import traceback as tb
import inspect

class CoreType(object):

    def __init__(self, *args, **kwargs):
        self.__valuetype__ = kwargs.pop('valuetype', None)
        if self.__valuetype__ == None:
            raise NotImplementedError('You need to specify a valuetype in keyword args')

        # assume singleton if not overridden
        # self.__singleton = kwargs.pop('singleton', True)

        initvalue = None
        if len(args) > 0:
            initvalue = args[0]

        """
        _initvalues = list(initvalues)
            if len(_initvalues) > 1 and self.issingleton() == True:
                raise TypeError('cannot add more than one item to a singleton')
            else:
                for item in _initvalues:
        """
        self.__value__ = initvalue #None
        """
        if initvalue != None:
            if not isinstance(initvalue, self.__valuetype__):
                raise TypeError('item is not of type %s, got %s instead' % (self.__valuetype__, type(initvalue)))
            try:
                self.__validate__(initvalue)
            except ValueError as err:
                raise err
            self.__value__ = initvalue
        """

    # TODO valid alternative repr requirements (if any)
    def __repr__(self):
        return '%s' % self.__value__

    def __str__(self):
        return '%s' % self.__value__

    def __validate__(self, validatedict):
        """
        Abstract Validation method, must be implemented by sub-classes.
        Must raise a ValueError if the value does not match the criteria
        Look at gtool.type.common for examples
        """
        raise NotImplementedError('Please implement a __validate__ method for your class %s' % self.__class__)

    @classmethod
    def __convert__(cls, item):
        try:
            return cls.__convertor__()(item)
        except ValueError:
            raise ValueError('cannot convert %s to type %s' %(item, cls.__convertor__()))


    @property
    def regex(self):
        # TODO implement the ability to override the regex as a param (perhaps from the config file
        if hasattr(self, '__identifierRegex'):
            raise NotImplementedError('You need to specify a regex for file matching in descendant class %s' % self.__class__)
        else:
            print(self.__identifierRegex)

    # ==== MAGIC METHODS OVERRIDE ====
    """
    def append(self, item):
        print('append should not be a supported operation on types - attribute should handle lists of types')
        if self.issingleton() and len(self) > 0:
            raise TypeError('cannot add another item to a singleton')
        if self.listtype == None:
            raise NotImplementedError('You need to init self.listtype')
        if not isinstance(item, self.listtype):
            raise TypeError('item is not of type %s' % self.listtype)
        try:
            self.__validate__(item)
        except ValueError as err:
            raise ValueError(err)
        self.__list.append(item)  # append the item to itself (the list)

    # TODO implement other magic methods (if needed)


    def __getitem__(self, index):
        #print('index: ', index)
        if type(index) is not int:
            #print(tb.print_exc())
            curframe = inspect.currentframe()
            calframe = inspect.getouterframes(curframe, 2)
            #print('caller name:', calframe[1][3])
            raise TypeError('indices must be integers or slides, not %s' % type(index))
        if not index + 1 < self.__len__():
            raise IndexError('index out of range')
        return self.__list[index]

    def __len__(self):
        return len(self.__list)

    def __add__(self, other):
        if not isinstance(other, type(self)):
            raise TypeError('cannot add an other of type %s to a %s' % (type(other), type(self)))
        try:
            _ = iter(other)
        except TypeError:
            raise TypeError('In %s: %s is not iterable (contents: "%s")' % (type(other), other))
        if self.listtype == None:
            raise NotImplementedError('You need to init self.listtype')
        for i, item in enumerate(other):
            if not isinstance(item, self.listtype):
                raise TypeError('item %s in other list is not of type %s' % (i, self.listtype))
        _templist = copy(self.__list)
        _templist.extend(other)
        return type(self)(_templist)

        # TODO investigate if this is pattern is correct
        temp = copy(self)
        for item in other:
            temp.append(item)
        return temp

    def __radd__(self, other):
        if not isinstance(other, type(self)):
            raise TypeError('cannot add a %s to other of type %s to' % (type(self), type(other)))
        try:
            _ = iter(other)
        except TypeError:
            raise TypeError('In %s: %s is not iterable (contents: "%s")' % (type(other), other))
        if self.listtype == None:
            raise NotImplementedError('You need to init self.listtype')
        for i, item in enumerate(other):
            if not isinstance(item, self.listtype):
                raise TypeError('item %s in other list is not of type %s' % (i, self.listtype))
        # TODO investigate if this is pattern is correct
        _templist = copy(other.__list) #
        _templist.extend(self.__list)
        return type(self)(_templist)

    def __iadd__(self, other):
        if not isinstance(other, type(self)):
            raise TypeError('cannot add an other of type %s to a %s' % (type(other), type(self)))
        try:
            _ = iter(other)
        except TypeError:
            raise TypeError('In %s: %s is not iterable (contents: "%s")' % (type(other), other))
        if self.listtype == None:
            raise NotImplementedError('You need to init self.listtype')
        for i, item in enumerate(other):
            if not isinstance(item, self.listtype):
                raise TypeError('item %s in other list is not of type %s' % (i, self.listtype))
        self.__list.extend(other.__list)
        return self
    """
