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
 def test_password(self):
  p=server.pwd_hash('password12345');self.assertTrue(server.pwd_verify('password12345',p));self.assertFalse(server.pwd_verify('wrong',p))
if __name__=='__main__':unittest.main()
