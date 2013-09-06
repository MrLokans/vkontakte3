#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import time
import json
import urllib.parse
import urllib.request
from hashlib import md5
from functools import partial


API_URL = 'http://api.vk.com/api.php'
SECURE_API_URL = 'https://api.vkontakte.ru/method/'
DEFAULT_TIMEOUT = 1
REQUEST_ENCODING = 'utf-8'
COMPLEX_METHODS = ['secure', 'ads', 'messages', 'likes', 'friends',
    'groups', 'photos', 'wall', 'newsfeed', 'notifications', 'audio',
    'video', 'docs', 'places', 'storage', 'notes', 'pages',
    'activity', 'offers', 'questions', 'subscriptions',
    'users', 'status', 'polls', 'account', 'auth', 'stats']


class VKError(Exception):
    __slots__ = ["error"]
    def __init__(self, error_data):
        Exception.__init__(self, str(self))

    @property
    def code(self):
        return self.error['error_code']

    @property
    def description(self):
        return self.error['error_msg']

    @property
    def params(self):
        return self.error['request_params']

    def __str__(self):
        return "Error (code = '%s', description = '%s', params = '%s')" % (self.code, self.description, self.params)


def _encode(s):
    if isinstance(s, (dict, list, tuple)):
        s = json.dumps(s, ensure_ascii = False)

    if isinstance(s, str):
        s = s.encode(REQUEST_ENCODING)

    return s


def signature(api_secret, params):
    keys = sorted(params.keys())
    param_str = "".join(["%s=%s" % (str(key), params[key]) for key in keys])
    return(md5(_encode(param_str + str(api_secret))).hexdigest())


class _API:
    def __init__(self, api_id = None, api_secret = None, token = None, **defaults):
        if not (api_id and api_secret or token):
            raise ValueError("Arguments api_id and api_secret or token are required")
        self.api_id = api_id
        self.api_secret = api_secret
        self.token = token
        self.defaults = defaults
        self.method_prefix = ''

    def __call__(self, **kwargs):
        method = kwargs.pop('method')
        params = self.defaults.copy()
        params.update(kwargs)
        return self._get(self.method_prefix + method, **params)

    def __getattr__(self, name):
        if name in COMPLEX_METHODS:
            api = _API(api_id=self.api_id, api_secret=self.api_secret, token=self.token, **self.defaults)
            api.method_prefix = name + '.'
            return api

        return partial(self, method = name)

    def _signature(self, params):
        return signature(self.api_secret, params)

    def _get(self, method, timeout=DEFAULT_TIMEOUT, **kwargs):
        response = str(self._request(method, timeout = timeout, **kwargs), REQUEST_ENCODING)
        data = json.loads(response, strict=False)
        if 'error' in data:
            raise VKError(data['error'])
        return data['response']


    def _request(self, method, timeout = DEFAULT_TIMEOUT, **kwargs):
        for key, value in list(kwargs.items()):
            kwargs[key] = _encode(value)

        if self.token:
            params = dict(
                access_token = self.token,
            )
            params.update(kwargs)
            params['timestamp'] = int(time.time())
            url = SECURE_API_URL + method
            secure = True
        else:
            params = dict(
                api_id = str(self.api_id),
                method = method,
                format = 'JSON',
                v = '3.0',
                random=random.randint(0, 2 ** 30),
            )
            params.update(kwargs)
            params['timestamp'] = int(time.time())
            params['sig'] = self._signature(params)
            url = API_URL
            secure = False
        data = urllib.parse.urlencode(params).encode(REQUEST_ENCODING)
        try: 
            res = urllib.request.urlopen(url=url, data=data, timeout=timeout)
        except URLError as e:
            raise VKError({
                'error_code': 404,
                'error_msg': e.reason,
                'request_params': kwargs,
            })
            res = ""
        except HTTPError as e:
            raise VKError({
                'error_code': e.code,
                'error_msg': 'HTTP error',
                'request_params': kwargs,
            })
            res = ""
        else:
            res = res.read()
        return res



class API(_API):
    def get(self, method, timeout=DEFAULT_TIMEOUT, **kwargs):
        return self._get(method, timeout, **kwargs)
    
    








