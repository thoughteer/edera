import abc
import base64
import inspect
import json

import iso8601
import six


class Serializable(object):
    """
    An object that can be serialized to an ASCII string and deserialized back.

    You need to define required fields in the class declaration.

    In order to make an abstract class serializable, please, use $AbstractSerializable instead.

    Examples:
        >>> class Record(Serializable):
        >>>     f = ListField(IntegerField)
        >>>     def __init__(self, f):
        >>>         self.f = f
        >>> record = Record([1, 2, 3])
        >>> Record.deserialize(record.serialize()).f
        [1, 2, 3]

    See also:
        $AbstractSerializable
        $Field
    """

    @classmethod
    def deserialize(cls, string):
        """
        Deserialize an object.

        Args:
            string (String)

        Returns:
            $cls - the deserialized object
        """
        data = json.loads(string)
        result = cls.__new__(cls)
        for name in data:
            field = getattr(result.__class__, name)
            setattr(result, name, field.load(data[name]))
        return result

    def serialize(self):
        """
        Serialize the object.

        Returns:
            String
        """
        data = {
            name: field.dump(getattr(self, name))
            for name, field in inspect.getmembers(self.__class__)
            if isinstance(field, Field)
        }
        return json.dumps(data)


class AbstractSerializableMeta(abc.ABCMeta):

    ___classes___ = {}

    def __new__(mcls, name, bases, body):
        cls = super(AbstractSerializableMeta, mcls).__new__(mcls, name, bases, body)
        AbstractSerializableMeta.___classes___[name] = cls
        return cls


@six.add_metaclass(AbstractSerializableMeta)
class AbstractSerializable(Serializable):
    """
    A $Serializable that can deserialize instances of derived classes.

    Examples:
        >>> class AbstractRecord(AbstractSerializable):
        >>>     @abc.abstractmethod
        >>>     def idle(self):
        >>>         pass
        >>> class Record(AbstractRecord):
        >>>     f = ListField(IntegerField)
        >>>     def __init__(self, f):
        >>>         self.f = f
        >>>     def idle(self):
        >>>         pass
        >>> record = Record([1, 2, 3])
        >>> AbstractRecord.deserialize(record.serialize()).f
        [1, 2, 3]
    """

    @classmethod
    def deserialize(cls, string):
        data = json.loads(string)
        origin = AbstractSerializableMeta.___classes___[data["?"]]
        return super(AbstractSerializable, origin).deserialize(data["!"])

    def serialize(self):
        data = {
            "?": self.__class__.__name__,
            "!": super(AbstractSerializable, self).serialize(),
        }
        return json.dumps(data)


@six.add_metaclass(abc.ABCMeta)
class Field(object):

    @abc.abstractmethod
    def dump(self, value):
        """
        Convert the value to a string.

        Args:
            value (Any)

        Returns:
            String
        """

    @abc.abstractmethod
    def load(self, string):
        """
        Convert the string back to a value.

        Args:
            string (String)

        Returns:
            Any
        """


class BooleanField(Field):

    def dump(self, value):
        return "true" if value else "false"

    def load(self, string):
        assert string in ("false", "true")
        return string == "true"

BooleanField = BooleanField()


class DateTimeField(Field):

    def dump(self, value):
        return value.isoformat()

    def load(self, string):
        return iso8601.parse_date(string)

DateTimeField = DateTimeField()


class IntegerField(Field):

    def dump(self, value):
        return str(value)

    def load(self, string):
        return int(string)

IntegerField = IntegerField()


class GenericField(Field):

    def __init__(self, cls):
        self.cls = cls

    def dump(self, value):
        return value.serialize()

    def load(self, string):
        return self.cls.deserialize(string)


class ListField(Field):

    def __init__(self, element_field):
        self.element_field = element_field

    def dump(self, value):
        return json.dumps([self.element_field.dump(element) for element in value])

    def load(self, string):
        return [
            self.element_field.load(element)
            for element in json.loads(string)
        ]


class MappingField(Field):

    def __init__(self, key_field, element_field):
        self.key_field = key_field
        self.element_field = element_field

    def dump(self, value):
        return json.dumps(
            {
                self.key_field.dump(key): self.element_field.dump(element)
                for key, element in six.iteritems(value)
            })

    def load(self, string):
        return {
            self.key_field.load(key): self.element_field.load(element)
            for key, element in six.iteritems(json.loads(string))
        }


class OptionalField(Field):

    def __init__(self, element_field):
        self.element_field = element_field

    def dump(self, value):
        return json.dumps(None if value is None else self.element_field.dump(value))

    def load(self, string):
        data = json.loads(string)
        return None if data is None else self.element_field.load(data)


class SetField(ListField):

    def load(self, string):
        return set(super(SetField, self).load(string))


class StringField(Field):

    def dump(self, value):
        return value

    def load(self, string):
        return string

StringField = StringField()


class TupleField(Field):

    def __init__(self, *element_fields):
        self.element_fields = element_fields

    def dump(self, value):
        return json.dumps(
            [
                element_field.dump(element)
                for element_field, element in zip(self.element_fields, value)
            ])

    def load(self, string):
        return tuple(
            element_field.load(element)
            for element_field, element in zip(self.element_fields, json.loads(string)))
