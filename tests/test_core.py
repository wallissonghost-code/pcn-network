import os,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
class TestCore(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();server.DB=Path(self.temp.name)/'test.sqlite3';server.init()
  with server.conn() as c:c.execute('INSERT INTO users(email,password,created) VALUES(?,?,?)',('a@b.com','test',0))
 def tearDown(self):self.temp.cleanup()
 def test_lifecycle_and_no_double_claim(self):
  with server.conn() as c:
   c.execute('BEGIN IMMEDIATE');r,s=server.start(c,1,100000);self.assertEqual(s,200);c.execute('COMMIT')
   c.execute('BEGIN IMMEDIATE');r,s=server.claim(c,1,100001);self.assertEqual(s,409);c.execute('ROLLBACK')
   c.execute('BEGIN IMMEDIATE');r,s=server.claim(c,1,100000+86400);self.assertEqual(s,200);self.assertEqual(r['claimed'],2.4);c.execute('COMMIT')
   c.execute('BEGIN IMMEDIATE');r,s=server.claim(c,1,100000+86401);self.assertEqual(s,409);c.execute('ROLLBACK')
 def test_global_supply_cap(self):
  original=server.MAX_SUPPLY
  try:
   server.MAX_SUPPLY=1_000000
   with server.conn() as c:
    c.execute('BEGIN IMMEDIATE');server.start(c,1,100000);c.execute('COMMIT')
    c.execute('BEGIN IMMEDIATE');r,status=server.claim(c,1,186400);c.execute('COMMIT')
    self.assertEqual(status,200);self.assertEqual(r['claimed'],1.0)
  finally:server.MAX_SUPPLY=original
 def test_login_throttle_persists(self):
  now=1000
  for i in range(server.MAX_LOGIN_ATTEMPTS):
   self.assertTrue(server.auth_attempt_allowed('test-ip','login',now))
   server.record_auth_attempt('test-ip','login',now)
  self.assertFalse(server.auth_attempt_allowed('test-ip','login',now))
  self.assertTrue(server.auth_attempt_allowed('test-ip','login',now+server.LOGIN_WINDOW+1))
 def test_registration_throttle(self):
  now=1000
  for i in range(server.MAX_REGISTRATIONS):
   self.assertTrue(server.auth_attempt_allowed('signup-ip','register',now))
   server.record_auth_attempt('signup-ip','register',now)
  self.assertFalse(server.auth_attempt_allowed('signup-ip','register',now))
  self.assertTrue(server.auth_attempt_allowed('signup-ip','register',now+server.LOGIN_WINDOW+1))
 def test_referral_tracking_no_rewards(self):
  with server.conn() as c:
   code=server.ensure_referral_code(c,1)
   self.assertEqual(server.ensure_referral_code(c,1),code)
   c.execute('INSERT INTO users(email,password,created) VALUES(?,?,?)',('invited@example.com','test',0))
   c.execute('INSERT INTO referrals(invited_id,inviter_id,created) VALUES(?,?,?)',(2,1,1000))
   self.assertEqual(c.execute('SELECT COUNT(*) FROM referrals WHERE inviter_id=1').fetchone()[0],1)
   self.assertEqual(c.execute('SELECT COALESCE(SUM(amount),0) FROM ledger').fetchone()[0],0)
 def test_admin_access_and_stats(self):
  old=os.environ.get('PCN_ADMIN_EMAIL')
  try:
   os.environ['PCN_ADMIN_EMAIL']='a@b.com'
   with server.conn() as db:
    self.assertTrue(server.is_admin(db,1))
    self.assertEqual(server.admin_stats(db,100000)['users'],1)
    self.assertEqual(server.admin_stats(db,100000)['issued_pcn'],0)
   os.environ['PCN_ADMIN_EMAIL']='other@example.com'
   with server.conn() as db:self.assertFalse(server.is_admin(db,1))
  finally:
   if old is None:os.environ.pop('PCN_ADMIN_EMAIL',None)
   else:os.environ['PCN_ADMIN_EMAIL']=old
 def test_password(self):
  p=server.pwd_hash('password12345');self.assertTrue(server.pwd_verify('password12345',p));self.assertFalse(server.pwd_verify('wrong',p))
if __name__=='__main__':unittest.main()
