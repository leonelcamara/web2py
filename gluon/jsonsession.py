#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Session implementation prototypes that only allow JSON and have a reasonable method
to know if it was modified.

Right now it only loads strings and return strings if saved to be easy to test and benchmark.
"""
import json


class TrackingDict(dict):
    
    def __init__(self, session, *args, **kwargs):
        self.session = session
        super(TrackingDict, self).__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        self.session._dirty = True
        super(TrackingDict, self).__setitem__(key, value)

    def __delitem__(self, key):
        self.session._dirty = True
        super(TrackingDict, self).__delitem__(key)

    def clear(self, *args, **kwargs):
        self.session._dirty = True
        super(TrackingDict, self).clear(*args, **kwargs)

    def pop(self, *args, **kwargs):
        self.session._dirty = True
        super(TrackingDict, self).pop(*args, **kwargs)

    def popitem(self, *args, **kwargs):
        self.session._dirty = True
        super(TrackingDict, self).popitem(*args, **kwargs)

    def update(self, *args, **kwargs):
        self.session._dirty = True
        super(TrackingDict, self).update(*args, **kwargs)


class TrackingList(list):

    def __init__(self, session, *args, **kwargs):
        self.session = session
        super(TrackingList, self).__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        self.session._dirty = True
        super(TrackingList, self).__setitem__(key, value)

    def __delitem__(self, key):
        self.session._dirty = True
        super(TrackingList, self).__delitem__(key)
    
    def append(self, *args, **kwargs):
        self.session._dirty = True
        super(TrackingList, self).append(*args, **kwargs)

    def extend(self, *args, **kwargs):
        self.session._dirty = True
        super(TrackingList, self).extend(*args, **kwargs)

    def insert(self, *args, **kwargs):
        self.session._dirty = True
        super(TrackingList, self).insert(*args, **kwargs)

    def pop(self, *args, **kwargs):
        self.session._dirty = True
        super(TrackingList, self).pop(*args, **kwargs)

    def remove(self, *args, **kwargs):
        self.session._dirty = True
        super(TrackingList, self).reverse(*args, **kwargs)

    def reverse(self, *args, **kwargs):
        self.session._dirty = True
        super(TrackingList, self).reverse(*args, **kwargs)

    def sort(self, *args, **kwargs):
        self.session._dirty = True
        super(TrackingList, self).sort(*args, **kwargs)



class MarkDirtySession(dict):

    __getitem__ = dict.get
    __getattr__ = dict.get

    def load(self, json_string):
        mysession = self

        class TrackingDecoder(json.JSONDecoder):

            def __init__(self, *args, **kwargs):
                json.JSONDecoder.__init__(self, *args, **kwargs)
                # Use the custom JSONArray
                self.parse_array = self.JSONArray
                self.parse_object = self.JSONObject
                self.scan_once = json.scanner.py_make_scanner(self) 

            def JSONArray(self, *args, **kwargs):
                values, end = json.decoder.JSONArray(*args, **kwargs)
                return TrackingList(mysession, values), end

            def JSONObject(self, *args, **kwargs):
                pairs, end = json.decoder.JSONObject(*args, **kwargs)
                return TrackingDict(mysession, pairs), end

        self.update(json.loads(json_string, cls=TrackingDecoder))

    def save(self):
        if self._dirty:
            dict.__delitem__(self, '_dirty')
            return json.dumps(self)
        return None

    def __setattr__(self, key, value):
        return self.__setitem__(key, value)

    def __delattr__(self, key):
        return self.__delitem__(self, key)

    def __setitem__(self, key, value):
        dict.__setitem__(self, '_dirty', True)
        return dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        dict.__setitem__(self, '_dirty', True)
        return dict.__delitem__(self, key)



if __name__ == '__main__':
    session = MarkDirtySession()
    session.load('{"a": 1, "b": 2}')
    assert session.a == 1
    assert session.save() is None
    session.a = 2
    assert session.save() == '{"a": 2, "b": 2}'
    session = MarkDirtySession()
    session.load('{"a": {"a": 1, "b": 2}, "b": 2}')
    session.a['a'] = 3
    assert session.save() == '{"a": {"a": 3, "b": 2}, "b": 2}'
    session.a.update({'c':3, 'd': 4})
    assert session._dirty
    session = MarkDirtySession()
    session.load('{"a": [1,2,3]}')
    session.a[2] = 2
    assert session.save() == '{"a": [1, 2, 2]}'