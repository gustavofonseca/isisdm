#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# ISIS-DM: the ISIS Data Model API
#
# Copyright (C) 2010 BIREME/PAHO/WHO
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 2.1 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from .ordered import OrderedProperty, OrderedModel
from .subfield import CompositeString
import json
import colander

class Document(OrderedModel):

    def __init__(self, **kwargs):
        super(Document, self).__init__(**kwargs)
        self.validate()

    def validate(self):
        for prop in self:
            descriptor = self.__class__.__getattribute__(self.__class__, prop)
            descriptor.validate(self, getattr(self, prop, None))

    @classmethod
    def get_schema(cls):
        schema = colander.SchemaNode(colander.Mapping())
        for prop in cls:

            '''
            if isinstance(cls.__dict__[prop], TextProperty):
                colander_type = colander.String()
            elif isinstance(cls.__dict__[prop], MultiTextProperty):
                colander_type = colander.Sequence()
            else:
                raise ValueError('Unknown property type "%s"' % type(prop))
            '''

            descriptor = cls.__getattribute__(cls, prop)
            colander_type = descriptor._colander_schema(cls, getattr(cls, prop, None))
            schema.add(colander.SchemaNode(colander_type, name=prop))


        return schema

    def to_python(self):
        '''
        generate a python representation for Document type classes
        '''
        properties = {}
        for prop in self:
            descriptor = self.__class__.__getattribute__(self.__class__, prop)
            properties[prop] = descriptor._pystruct(self, getattr(self, prop, None))
        return properties

    @classmethod
    def from_python(cls, pystruct):
        if cls.__name__ != pystruct.pop('type'):
            raise TypeError()

        isisdm_pystruct = dict((str(k), tuple(v) if isinstance(v, list) else v)
            for k, v in pystruct.items())

        return cls(**isisdm_pystruct)

class Invalid(Exception):
    ''' TODO: study colander.Invalid exception '''
    def __init__(self, message):
        super(Exception, self).__init__(message)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.message)


class CheckedProperty(OrderedProperty):

    def __init__(self, required=False, validator=None, choices=None):
        super(CheckedProperty, self).__init__()
        self.required = required
        self.validator = validator
        self.choices = choices if choices else []

    def __set__(self, instance, value):
        if self.validator:
            self.validator(self, value)
        super(CheckedProperty, self).__set__(instance, value)

    def validate(self, instance, value):
        if self.missing(instance):
            raise TypeError('required %r property missing' % self.name)
        if value is not None and self.validator:
            self.validator(self, value)

    def missing(self, instance):
        # a property is missing if it is required and
        # does not exist or is set to None
        # if it is not required, it is never missing
        return self.required and getattr(instance, self.name, None) is None


class TextProperty(CheckedProperty):

    def __set__(self, instance, value):
        if not isinstance(value, basestring):
            raise TypeError('%r value must be unicode or str instance' % self.name)
        value = unicode(value)
        if self.required and len(value.rstrip()) == 0:
            raise Invalid('%r value cannot be empty' % self.name)
        super(TextProperty, self).__set__(instance, value)

    def _pystruct(self, instance, value):
        '''
        python representation for this property
        '''
        return value

    def _colander_schema(self, instance, value):
        return colander.String()

class MultiTextProperty(CheckedProperty):

    def __set__(self, instance, value):
        if not isinstance(value, tuple):
            raise TypeError('MultiText value must be tuple')
        super(MultiTextProperty, self).__set__(instance, value)

    def _pystruct(self, instance, value):
        '''
        python representation for this property
        '''
        return value

    def _colander_schema(self, instance, value):
        return colander.Sequence()

class CompositeTextProperty(CheckedProperty):

    def __init__(self, subkeys=None, **kwargs):
        super(CompositeTextProperty, self).__init__(**kwargs)
        self.subkeys = subkeys

    def __set__(self, instance, value):
        if not isinstance(value, basestring):
            raise TypeError('%r value must be unicode or str instance' % self.name)

        composite_text = CompositeString(value, self.subkeys)
        super(CompositeTextProperty, self).__set__(instance, composite_text)

    def _pystruct(self, instance, value):
        '''
        python representation for this property
        '''
        return value.items()

    def _colander_schema(self, instance, value):
        schema = colander.SchemaNode(Tuple())
        schema.add(colander.SchemaNode(colander.String()), name='subkey')
        schema.add(colander.SchemaNode(colander.String()), name='value')
        return schema

class MultiCompositeTextProperty(CheckedProperty):

    def __init__(self, subkeys=None, **kwargs):
        super(MultiCompositeTextProperty, self).__init__(**kwargs)
        self.subkeys = subkeys

    def __set__(self, instance, value):
        if not isinstance(value, tuple):
            raise TypeError('MultiCompositeText value must be tuple')

        composite_texts = tuple(CompositeString(raw_composite_text, self.subkeys) for raw_composite_text in value)
        super(MultiCompositeTextProperty, self).__set__(instance, composite_texts)

    def _pystruct(self, instance, value):
        '''
        python representation for this property
        '''
        return tuple(composite_text.items() for composite_text in value)

class ReferenceProperty(CheckedProperty):

    def __set__(self, instance, value):
        if not isinstance(value, basestring):
            raise TypeError('Reference value must be unicode or str instance')
        value = unicode(value)
        if self.required and len(value.rstrip()) == 0:
            raise Invalid('%r value cannot be empty' % self.name)
        super(ReferenceProperty, self).__set__(instance, value)

    def _pystruct(self, instance, value):
        '''
        python representation for this property
        '''
        return value

if __name__ == '__main__':
    import doctest
    doctest.testmod()
