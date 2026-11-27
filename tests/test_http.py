import json
import os
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


class ApiIntegration(unittest.TestCase):
 def setUp(self):
  self.temp = tempfile.TemporaryDirectory()
  self.old_db = server.DB
  self.old_beta = os.environ.get('PCN_PRIVATE_BETA')
  self.old_admin = os.environ.get('PCN_ADMIN_USER_ID')
  server.DB = Path(self.temp.name) / 'integration.sqlite3'
  server.init()
  os.environ['PCN_PRIVATE_BETA'] = '0'
  os.environ.pop('PCN_ADMIN_USER_ID', None)
  self.http = ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
  self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
  self.thread.start()
  self.base = 'http://127.0.0.1:' + str(self.http.server_port)

 def tearDown(self):
  self.http.shutdown()
  self.http.server_close()
  self.thread.join(timeout=5)
  server.DB = self.old_db
  if self.old_beta is None: os.environ.pop('PCN_PRIVATE_BETA', None)
  else: os.environ['PCN_PRIVATE_BETA'] = self.old_beta
  if self.old_admin is None: os.environ.pop('PCN_ADMIN_USER_ID', None)
  else: os.environ['PCN_ADMIN_USER_ID'] = self.old_admin
  self.temp.cleanup()

 def request(self, path, data=None, token=None):
  headers = {'Content-Type': 'application/json'}
  if token: headers['Authorization'] = 'Bearer ' + token
  payload = None if data is None else json.dumps(data).encode()
  req = Request(self.base + path, data=payload, headers=headers)
  try:
   with urlopen(req, timeout=5) as response:
    return response.status, json.load(response)
  except HTTPError as e:
   return e.code, json.load(e)

 def test_register_login_referral_and_admin_authorization(self):
  status, owner = self.request('/api/register', {'email':'owner@example.com','password':'secure-password-123'})
  self.assertEqual(status, 200)
  token = owner['token']
  status, ref = self.request('/api/referrals', token=token)
  self.assertEqual(status, 200)
  status, _ = self.request('/api/admin/stats', token=token)
  self.assertEqual(status, 403)
  status, invited = self.request('/api/register', {'email':'invited@example.com','password':'secure-password-456','referral':ref['code']})
  self.assertEqual(status, 200)
  status, ref = self.request('/api/referrals', token=token)
  self.assertEqual(ref['invited_count'], 1)
  os.environ['PCN_ADMIN_USER_ID'] = '1'
  status, stats = self.request('/api/admin/stats', token=token)
  self.assertEqual(status, 200)
  self.assertEqual(stats['users'], 2)
  status, _ = self.request('/api/admin/stats', token=invited['token'])
  self.assertEqual(status, 403)

 def test_private_beta_blocks_registration(self):
  os.environ['PCN_PRIVATE_BETA'] = '1'
  status, _ = self.request('/api/register', {'email':'x@example.com','password':'secure-password-123'})
  self.assertEqual(status, 403)

 def test_login_failure_returns_401_not_500(self):
  status, _ = self.request('/api/login', {'email':'missing@example.com','password':'secure-password-123'})
  self.assertEqual(status, 401)

 def test_health_and_network(self):
  status, data = self.request('/api/health')
  self.assertEqual(status, 200)
  self.assertEqual(data['status'], 'ok')
  status, data = self.request('/api/network')
  self.assertEqual(status, 200)
  self.assertTrue(data['simulation'])


if __name__ == '__main__':
 unittest.main()
