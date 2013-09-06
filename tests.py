#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests for vkontakte package.
"""

import unittest
import unittest.mock
import urllib.request
import urllib.response
import urllib.parse
import json
import vkontakte
import vkontakte.api

API_ID = 'api_id'
API_SECRET = 'api_secret'


class VkontakteTest(unittest.TestCase):
    def test_api_creation_error(self):
        self.assertRaises(ValueError, lambda: vkontakte.API())

class SignatureTest(unittest.TestCase):
    def test_signature_supports_unicode(self):
        params = {'foo': 'клен'}
        self.assertEqual(
            vkontakte.signature(API_SECRET, params), 
            '560b3f1e09ff65167b8dc211604fed2b'
        )

class VkontakteMagicTest(unittest.TestCase):
    def setUp(self):
        self.api = vkontakte.API(API_ID, API_SECRET)

    @unittest.mock.patch('vkontakte.api._API._get')
    def test_basic(self, _get):
        _get.return_value = '123'
        time = self.api.getServerTime()
        self.assertEqual(time, '123')
        _get.assert_called_once_with('getServerTime')

    @unittest.mock.patch('vkontakte.api._API._get')
    def test_with_arguments(self, _get):
        _get.return_value = ["{'last_name': u'Дуров'}"]
        res = self.api.getProfiles(uids='1,2', fields='education')
        self.assertEqual(res, _get.return_value)
        _get.assert_called_once_with('getProfiles', uids='1,2', fields='education')

    @unittest.mock.patch('vkontakte.api._API._get')
    def test_with_arguments_get(self, _get):
        _get.return_value = [{'last_name': u'Дуров'}]
        res = self.api.get('getProfiles', uids='1,2', fields='education')
        self.assertEqual(res, _get.return_value)
        _get.assert_called_once_with('getProfiles', vkontakte.api.DEFAULT_TIMEOUT, uids='1,2', fields='education')

    @unittest.mock.patch('vkontakte.api._API._request')
    def test_timeout(self, _request):
        _request.return_value = b'{"response":123}'
        api = vkontakte.API(API_ID, API_SECRET, timeout=5)
        res = api.getServerTime()
        self.assertEqual(res, 123)

    @unittest.mock.patch('vkontakte.api._API._get')
    def test_magic(self, _get):
        for method in vkontakte.api.COMPLEX_METHODS:
            _get.return_value = None
            res = getattr(self.api, method).test()
            self.assertEqual(res, None)
            _get.assert_called_once_with('%s.test' % method)
            _get.reset_mock()

    @unittest.mock.patch('vkontakte.api._API._get')
    def test_magic_get(self, _get):
        _get.return_value = 'foo'
        res = self.api.friends.get(uid=642177)
        self.assertEqual(res, 'foo')
        _get.assert_called_once_with('friends.get', uid=642177)

    @unittest.mock.patch('vkontakte.api._API._request')
    def test_urlencode_bug(self, _request):
        _request.return_value = b'{"response":123}'
        res = self.api.search(q='клен')
        self.assertEqual(res, 123)

    @unittest.mock.patch('vkontakte.api._API._request')
    def test_valid_quoted_json(self, _request):
        _request.return_value = b'{"response": 123}'
        self.api.ads.getStat(data={'type': '1', 'id': 1})
        print(urllib.parse.unquote(json.dumps(_request.call_args[1]['data'])))
        posted_data = urllib.parse.unquote(json.dumps(_request.call_args[1]['data']))
        self.assertTrue('{"id":+1,+"type":+"1"}' in posted_data, posted_data)


if __name__ == '__main__':
    unittest.main()
