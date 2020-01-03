import os
import json
import logging
import re
import datetime

logger = logging.getLogger(__name__)


class MetaField(object):
    """
    A class to extract a value from recording

    :param name:    The recording field name
    :param scaling: If int/float: field value will be casted as
                    int/float and scaled by given value
                    If string: field will be interpreted as string
                    If dictionary: field value will be choosen from 
                    dictionary items
    :param default: value to return if such field is not defined 
                    or don't have a value
    """

    __slots__ = ["name", "scaling", "default", "__value", "__get"]

    def __init__(self, name, scaling="str", default=None):
        self.name = name
        self.scaling = scaling
        self.default = default
        self.__value = default

        if scaling is None:
            self.__get = self.__get_raw
        else:
            if isinstance(scaling, int):
                self.__get = self.__get_int
            elif isinstance(scaling, float):
                self.__get = self.__get_float
            elif isinstance(scaling, str):
                self.__get = self.__get_str
            elif isinstance(scaling, dict):
                self.__get = self.__get_select
            else:
                raise ValueError("Can't determine type of field from '{}'"
                                 .format(scaling))

    def __bool__(self):
        if self.value:
            return True
        else:
            return False

    def __get_raw(self, value):
        self.__value = value

    def __get_int(self, value):
        self.__value = int(value) * self.scaling

    def __get_float(self, value):
        self.__value = float(value) * self.scaling

    def __get_str(self, value):
        self.__value = str(value).strip()

    def __get_select(self, value):
        if value in self.scaling:
            return self.scaling[value]
        else:
            logger.warning("Invalid value {} for field {}"
                           .format(value, self.name))
            return None

    @property
    def value(self):
        return self.__value
    
    @value.setter
    def value(self, value):
        if value is None or value == "":
            self.__value = self.default
        else:
            self.__get(value)


class fieldEntry(object):
    """
    object containing a dictionary defining a given field in BIDS
    formatted .tsv file. This dictionary will be written into
    corresponding json file.
    """
    __slots__ = ["__name", "__values", "__activated"]

    def __init__(self, name, longName="", description="",
                 levels={}, units="", url="", activate=True):
        """
        constructor

        Parameters
        ----------
        name : str
            an id of a field, must be non-empty and composed only of
            [0-9a-zA-Z_]
        longName : str
            long (unabbreviated) name of the column.
        description : str
            description of the column
        levels : dict
            For categorical variables: 
            a dictionary of possible values (keys) 
            and their descriptions (values).
        units : str
            measurement units. [<prefix symbol>] <unit symbol> format 
            following the SI standard is RECOMMENDED. See
            https://bids-specification.readthedocs.io/en/latest/\
                    99-appendices/05-units.html
        url : str
            URL pointing to a formal definition of this type of data 
            in an ontology available on the web
        activate : bool
            will be created field activated or not

        Raises
        ------
        TypeError
            if passed parameters of incorrect type
        ValueError
            if name is invalid (empty or contains forbidden character)
        """
        if not isinstance(name, str):
            raise TypeError("name must be a string")
        if not isinstance(longName, str):
            raise TypeError("longName must be a string")
        if not isinstance(description, str):
            raise TypeError("description must be a string")
        if not isinstance(units, str):
            raise TypeError("units must be a string")
        if not isinstance(url, str):
            raise TypeError("url must be a string")
        if not isinstance(activate, bool):
            raise TypeError("activate must be a bool")
        if not isinstance(levels, dict):
            raise TypeError("levels must be a dictionary")
        m = re.fullmatch('\\w*', name)
        if name == "" or m is None:
            raise ValueError("name '{}' is invalid".format(name))

        self.__name = name
        self.__values = dict()

        if longName != "":
            self.__values["LongName"] = longName
        if description != "":
            self.__values["Description"] = description
        if len(levels) > 0:
            self.__values["Levels"] = levels
        if units != "":
            self.__values["Units"] = units
        if url != "":
            self.__values["TermURL"] = url
        self.__activated = activate

    def Active(self):
        """
        returns activated status
        """
        return self.__activated

    def GetName(self):
        return self.__name

    def GetValues(self):
        return self.__values

    def __eq__(self, other):
        """
        definition of equality (==) operator by the name of field
        """
        if not isinstance(other, fieldEntry):
            raise TypeError("comparaison must be between same type")
        return self.__name == other.__name


class BIDSfieldLibrary(object):
    """
    a library class for fields used in BIDS tsv files.

    In order to an object to use BIDS tsv fields, this object must 
    inherit from this class.

    It contains a static list of available fields, and a dynamic 
    dictionary of values for each of objects.

    A list of required and suggested fields must be added to library in 
    class definition (outside of __init__). User-defined fields can be 
    added in plugin at any point.

    Each field can be described by its id (name), explicit name, description,
    possible values and descriptive url. For more details, refer to BIDS 
    description there:
    https://bids-specification.readthedocs.io/\
en/latest/02-common-principles.html

    Each field can be activated or deactivated. Only acive fields will be
    reported in json and tsv filres.

    The descriptive json file is created by BIDSdumpJSON(filename)
    The header line is created by static method BIDSgetHeader()
    Data line for each instance is created by BIDSgetLine()
    """
    __slots__ = ["__library"]

    def __init__(self):
        """
        creator
        """
        self.__library = list()

    def AddField(self, name, longName="", description="", 
                 levels={}, units="", url="", activated=True):
        """
        append new field to library. The field name must be unique

        Parameters
        ----------
        name : str
            an id of a field, must be non-empty and composed only of
            [0-9a-zA-Z_]
        longName : str
            long (unabbreviated) name of the column.
        description : str
            description of the column
        levels : dict
            For categorical variables: 
            a dictionary of possible values (keys) 
            and their descriptions (values).
        units : str
            measurement units. [<prefix symbol>] <unit symbol> format 
            following the SI standard is RECOMMENDED. See
            https://bids-specification.readthedocs.io/en/latest/\
                    99-appendices/05-units.html
        url : str
            URL pointing to a formal definition of this type of data 
            in an ontology available on the web
        activate : bool
            will be created field activated or not

        Raises
        ------
        TypeError
            if passed parameters are of invalid type
        IndexError
            if name of field is already in dictionary
        """
        fe = fieldEntry(name, longName, description, 
                        levels, units, url, activated)
        if fe not in self.__library:
            self.__library.append(fe)
        else:
            raise IndexError("Field in library already contains " + name)

    def Activate(self, name, act=True):
        """
        change activated status of given field

        Parameters
        ----------
        name : str
            name of field to change status. Must exist in library
        act : bool
            status to set

        Raises
        ------
        TypeError
            if passed parameters are of incorrect type
        keyError
            if field not found in dictionary
        """
        if not isinstance(name, str):
            raise TypeError("name must be a string")
        if not isinstance(act, bool):
            raise TypeError("act must be bool")
        self.__library[name].__activated = act

    def GetNActive(self):
        """
        returns number of active fields
        """
        count = 0
        for f in self.__library:
            if f.Active(): count += 1
        return count

    def GetActive(self):
        """
        returns a list of names of active fields
        """
        active = [f.GetName() for f in self.__library if f.Active()]
        return active

    def GetHeader(self):
        """
        returns tab-separated string with names of activated
        fields. string does not contain new line.

        Returns
        -------
        str
            header line
        """
        line = [f.GetName() for f in self.__library if f.Active()]
        return ('\t'.join(line))

    def GetLine(self, values):
        """
        returns tab-separated string with given values. Values
        are searched by keys corresponding to active fields and
        normalized by Normalize function. Returned string does
        not contains new line and is conforms to BIDS, described
        there: https://bids-specification.readthedocs.io/en/\
latest/02-common-principles.html

        Parameters
        ----------
        values : dict, optional
            a dictionary of values with keys corresponding to fields 
            defined in library

        Returns
        -------
        str
            tab-separated string
        """ 
        if not isinstance(values, dict):
            raise TypeError("values must be a dictionary")
        active = self.GetActive() 
        result = list()
        for f in active:
            if f in values:
                result.append(self.Normalize(values[f]))
            else:
                result.append('n/a')
        return "\t".join(result)

    @staticmethod
    def Normalize(value):
        """
        adapt input value to format acceptable by BIDS tsv
        file. By default it transforms value to string using str(),
        then  it changes tab (\\t) and new line (\\n) to space.
        datetime types are transformed using isoformat, and 
        timedelta are expressed in seconds. Non-defined values
        (None) and empty strings are replaced by 'n/a'.

        Returns
        -------
        str
            normalized string
        """

        if value is None:
            return "n/a"
        v = ""
        if isinstance(value, datetime.datetime)\
           or isinstance(value, datetime.date)\
           or isinstance(value, datetime.time):
            v = value.isoformat()
        elif isinstance(value, datetime.timedelta):
            v = str(value.total_seconds())
        else:
            v = str(value).replace('\t', " ").replace('\n', " ")
        if v == "" : return "n/a"
        return v

    def GetTemplate(self):
        """
        returns a template dictionary for values with active fields 
        as keys and None as values
        """
        res = dict()
        for f in self.__library:
            res[f.GetName()] = None
        return res

    def DumpDefinitions(self, filename):
        """
        dump fields definitions to a json file. If file exists, it 
        will be replaced.

        Parameters
        ----------
        filename: str
            name of file to dump library

        Raises
        ------
        TypeError
            if passed parameters are of incorrect type
        """
        if not isinstance(filename, str):
            raise TypeError("filename must be a string")
        if filename[-5:] != ".json":
            raise ValueError("filename must end with '.json'")
        if os.path.isfile(filename):
            logger.warning("JSON file {} already exists. It will be replaced."
                           .format(filename))
        struct = dict()

        for f in self.__library:
            if f.Active():
                struct[f.GetName()] = f.GetValues()

        with open(filename, 'w') as f:
            json.dump(struct, f, indent="  ", separators=(',', ':'))
