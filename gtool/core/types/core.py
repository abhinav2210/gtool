from gtool.core.utils.output import formatternamespace
from gtool.core.filewalker import registerFileMatcher
from gtool.core.utils.misc import striptoclassname
from collections import defaultdict
from copy import deepcopy
import pyparsing as p
from gtool.core.plugin import pluginnamespace
from abc import abstractmethod

class CoreType(object):
    """
    CoreType is the base object for all attribute types (except user created classes)
    """

    def __init__(self, *args, **kwargs):
        self.__valuetype__ = kwargs.pop('valuetype', None)
        if self.__valuetype__ == None:
            raise NotImplementedError('You need to specify a valuetype in keyword args')

        # assume singleton if not overridden
        # self.__singleton = kwargs.pop('singleton', True)

        initvalue = None
        if len(args) > 0:
            initvalue = args[0]
        self.__value__ = initvalue #None

    # TODO valid alternative repr requirements (if any)
    def __repr__(self):
        #return '%s' % self.__value__
        #return '{0}: {1}'.format(striptoclassname(type(self)), self.__value__)
        return  '%s' % self.__convert__(self.__value__)

    def raw(self):
        return self.__convert__(self.__value__)

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
            return cls.__converter__()(item)
        except ValueError:
            raise ValueError('cannot convert %s to type %s' %(item, cls.__converter__()))


class DynamicType(object):
    """
    base object for dynamically generated classes
    """

    def __init__(self, **kwargs):
        # Deepcopy required otherwise list gets shared across instances of generated objects
        self.__list_slots__ = deepcopy(self.__list_slots__)
        self.kwargs = kwargs
        self.__context__ = None
        self.__createattrs__(self.kwargs)
        if not (isinstance(self, DynamicType)):
            # all dynamic classes must inherit from gtool's Dynamic type found in gtool.core.types.core
            raise TypeError(
                'The dynamic class %s was generated that does not inherit from gtool.types.core.DynamicType' % self.__class__)
        # print('mandatory properties for %s' % type(self), self.__mandatory_properties__)

        self.__missing_mandatory_properties__ = []
        self.__missing_optional_properties__ = []
        self.__method_results__ = {}

    # --- class methods that will be bound by factory ---
    # must be outside of class factory or they get factory's context and not the manufactured objects

    # TODO __createattrs__ code is similar to setattr code, can probably be shared

    def paramparser(params):
        # print(params)
        # TODO this is a lot of work we should really do in gtool.utils.config with pyparsing and return proper dicts
        _retDict = {}

        if 'kwargs' in params.keys():
            _retDict['kwargs'] = {k[0]: k[1] for k in params['kwargs']}
        else:
            _retDict['kwargs'] = {}

        # parallel implemtation, get rid of the kwargs.singleton once complete
        if 'singleton' in params.keys():
            _retDict['kwargs']['singleton'] = params['singleton']
            _retDict['singleton'] = params['singleton']

        if 'posargs' in params.keys():
            _retDict['posargs'] = [k for k in params['posargs']]

        return _retDict

    def __createattrs__(self, kwargs):
        for attribClass in self.__list_slots__.keys():
            # TODO these should be explicity passed in
            # TODO __line_slots__ should be a class to ensure data integrity
            # TODO we're assuming that that attribclass is properly setup... need to check before reading
            base = self.__list_slots__[attribClass]
            classObject = base.attrtype

            if attribClass in kwargs.keys():
                # if passed in arguments contains initialization data for an attribute, continue...
                args = self.kwargs[attribClass]
                try:
                    # if the init data is actually an object of the correct class
                    base.__load__(args)
                except TypeError as terr:
                    raise TypeError('In %s initialization of %s excepted %s but got %s and received: %s' % (
                        type(self), attribClass, classObject, type(args), terr))

    # TODO return some info about attribs
    def __repr__(self):
        #_dict = {prop: getattr(self, prop) for prop in self.dynamicproperties}
        _dict = {k:v for k, v in self}
        return '%s: %s' % (self.__class__, _dict)

    # TODO return some info about attribs
    def __str__(self):
        strclass = "%s" % self.__class__
        strclass = strclass.split('.')[-1:][0][:-2]
        _dict = {prop: getattr(self, prop) for prop in self.dynamicproperties}
        return '%s: %s' % (strclass, _dict)

    def __getattribute__(self, name):
        """
        an "anonymous" function that will be included into the dynamically generated class to made dynamically
        generated properties exist.
        :param self: object instance
        :param name: name of object attribute after the dot notation
        :return: list
        """
        try:
            listslots = object.__getattribute__(self, '__list_slots__')
            return listslots[name]
        except Exception:
            pass

        try:
            #self.__method_results__[name]
            methodresults = object.__getattribute__(self, '__method_results__')
            return methodresults[name]
        except Exception:
            return super(DynamicType, self).__getattribute__(name)

        #return object.__getattribute__(self, name)


    def __setattr__(self, attr, item):
        """
        Replace an existing dynamic property or set it. Will only allow the property to set with a fully
        formed object instance that matches the required dynamic properties set by classgen
        :param self:
        :param attr:
        :param item:
        :return:
        """

        if attr in self.__list_slots__.keys():
            self.__list_slots__[attr].__set__(item)
        # TODO find a way to throw an error if caller attempts to override method attrib
        #elif attr in self.__method_results__:
        #    raise AttributeError('%s is the output from a method plugin and cannot be set' % attr)
        else:
            # setting a method using dot notation (self.attr) will trigger recursion unless we have this
            # else handler
            #self.__dict__[attr] = item
            super(DynamicType, self).__setattr__(attr, item)

    @property
    def dynamicproperties(self):
        return self.__dynamic_properties__

    @property
    def mandatoryproperties(self):
        return self.__mandatory_properties__

    @property
    def missingproperties(self):
        return self.__missing_mandatory_properties__

    @property
    def missingoptionalproperties(self):
        return self.__missing_optional_properties__

    def loads(self, loadstring, softload=False, context=None): # TODO make use of context in error reporting
        """
        Method to read in a correctly structured string and load it into the object attributes
        :param loadstring:
        :return: True if data loaded
        """

        def parseLoadstring(loadstring):
            attributeStartMarker = p.LineStart() + p.Literal('@')
            attributeStopMarker = p.Literal(':')
            exp = attributeStartMarker.suppress() + p.Word(p.alphanums + '_') + attributeStopMarker.suppress()

            # ret = {}
            ret = defaultdict(list)

            for index, line in enumerate(loadstring.splitlines()):
                # print(line)
                # TODO switch from scanString to full parsing
                result = list(exp.scanString(line))
                if len(result) > 0:
                    # TODO this is kludgy
                    attribname = result[0][0][0]
                    matchstart = result[0][1]
                    matchend = result[0][2] + 1
                    if matchstart == 0:
                        # print('matched on line %s' % index)
                        # print('%s: %s' % (attribname, line[matchend:]))
                        ret[attribname].append(line[matchend:])
                    else:
                        raise Exception('attrib not at the start of the line')
                else:
                    # print('no match on line %s' % index)
                    # last = len(ret) - 1
                    ret[attribname][-1:] = [ret[attribname][-1:][0] + "" + line.strip()]

            return ret

        def convertandload(_self, attrname, attrval):
            cfunc = _self.__list_slots__[attrname].__convert__
            attrfunc = _self.__list_slots__[attrname].attrtype

            return [attrfunc(cfunc(s.strip())) for s in attrval]

        self.__context__ = context
        ret = parseLoadstring(loadstring)
        attriblist = [k for k in ret.keys()]
        # check if all attribs required by class definition are in the data file
        for prop in self.__dynamic_properties__:
            # TODO don't raise for non-mandatory attribs
            if prop not in attriblist:
                if prop in self.__mandatory_properties__ and softload is False:
                    raise AttributeError('attribute %s required by %s class definition file but not found' %
                                         (prop, self.__class__))
                if prop in self.__mandatory_properties__ and softload is True:
                    self.__missing_mandatory_properties__.append(prop)
                if prop not in self.__mandatory_properties__:
                    self.__missing_optional_properties__.append(prop)
        # reverse check of above and to ensure only attributes required by class file are present in data file
        for attrname, attrval in ret.items():
            if attrname not in self.__dynamic_properties__:
                raise AttributeError('attribute %s found in string but not in %s class definition file' %
                                     (attrname, self.__class__))
            else:
                # TODO load into object attribs
                # TODO pass in args (also refactor load so dict args are correct)
                try:
                    self.__list_slots__[attrname].__load__(convertandload(self, attrname, attrval))
                except Exception as err:
                    raise TypeError('got an error when trying to load data for %s: %s' % (self.__class__, err))

        for k, v in self.__methods__.items():
            modulename = v['module']
            _result = pluginnamespace()[modulename.upper()](self, config=v['config'], context=context)
            self.__method_results__[k] = _result.result

        return True if len(ret) > 0 else False

    def load(self, loadfile, softload=False):
        _ret = False

        context = {'file': loadfile, 'parent': None, 'class': type(self)} #also set in dataasobject

        # TODO make sure we can read file (in case it's large)
        try:
            f = open(loadfile, mode='r', newline="\n")
        except FileNotFoundError:
            raise FileNotFoundError('%s does not exist' % loadfile)
        except IOError:
            raise IOError('could not open %s' % loadfile)
        except Exception:
            raise Exception('attempted to to read %s and got an exception' % loadfile)
        else:
            try:
                _ret = self.loads(f.read(), softload=softload, context=context)
            except AttributeError as err:
                raise Exception('Reading %s: %s' % (loadfile, err))
            f.close()
            return _ret

    @classmethod
    def classfile(cls):
        if 'file' in cls.metas():
            return cls.__metas__.get('file')
        else:
            return None

    @classmethod
    def register(cls, classname):
        # only register if a file prefix is provided
        if cls.classfile() is not None:
            registerFileMatcher(cls.classfile(), classname)
        else:
            raise AttributeError('%s does not have a *file attribute defined' % classname)

    @classmethod
    def metas(cls):
        if hasattr(cls, '__metas__'):
            return cls.__metas__
        else:
            # print('has no metas')
            return None

    @classmethod
    def displayname(cls):
        return cls.metas()['displayname'] if 'displayname' in cls.metas() else '%s' % cls

    # TODO determine which methods from utils.classgen.methods can be moved in here

    def __classoutputscheme__(self):
        return formatternamespace()[striptoclassname(self.__class__)]

    def asdict(self):
        _retdict = {}
        for k, v in self:
            if not v.isdynamic:
                _v = [i.raw() for i in v]
            else:
                _v = [i.asdict() for i in v]
            _retdict[k] = _v
        return _retdict

    def __iter__(self):
        for item in self.__list_slots__.keys(): #TODO switch to .items
            _value = self.__list_slots__[item]
            yield (item, _value) # self.__list_slots__[item])

        for k, v in self.__method_results__.items():
            yield (k, v)


class FunctionType(object):

    @abstractmethod
    def __init__(self, obj, config=str()):
        """
        Based class for method plugins

        :param obj: the DynamicType Object that the function will operate one
        :param config: instructions on how the plugin should work. May be a list, dict or string
        """

        self.targetobject = obj
        self.config = config
        self.computable = False
        self.__result__ = None

    @abstractmethod
    def compute(self):
        if self.computable:
            return self.__result__

    @property
    def context(self):
        return self.__context__

    @property
    def result(self):
        self.compute()
        return self.__result__

    @abstractmethod
    def __repr__(self):
        return self.config

    def __str__(self):
        self.compute()
        return self.__result__