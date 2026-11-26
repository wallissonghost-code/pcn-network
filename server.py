import base64, hashlib, hmac, json, os, secrets, sqlite3, time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).parent
DB=Path(os.getenv('PCN_DB',str(ROOT/'pcn.sqlite3')))
SESSION=24*3600
MAX_LOGIN_ATTEMPTS=8
LOGIN_WINDOW=15*60
MAX_REGISTRATIONS=4

def auth_attempt_allowed(ip,kind,now):
 with conn() as c:
  c.execute('DELETE FROM auth_attempts WHERE created<?',(now-LOGIN_WINDOW,))
  n=c.execute('SELECT COUNT(*) FROM auth_attempts WHERE ip=? AND kind=? AND created>?',(ip,kind,now-LOGIN_WINDOW)).fetchone()[0]
 return n<(MAX_REGISTRATIONS if kind=='register' else MAX_LOGIN_ATTEMPTS)

def record_auth_attempt(ip,kind,now):
 with conn() as c:
  c.execute('INSERT INTO auth_attempts(ip,kind,created) VALUES(?,?,?)',(ip,kind,now))

DAILY_POOL=24000_000000
MAX_SUPPLY=100_000_000_000000

def conn():
 c=sqlite3.connect(DB,timeout=10,isolation_level=None)
 c.execute('PRAGMA journal_mode=WAL')
 c.execute('PRAGMA foreign_keys=ON')
 return c

def init():
 with conn() as c:
  c.executescript("""CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,email TEXT UNIQUE NOT NULL,password TEXT NOT NULL,created INTEGER NOT NULL);
  CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY,user_id INTEGER NOT NULL,expires INTEGER NOT NULL,FOREIGN KEY(user_id) REFERENCES users(id));
  CREATE TABLE IF NOT EXISTS mining(id INTEGER PRIMARY KEY,user_id INTEGER NOT NULL,started INTEGER NOT NULL,ends INTEGER NOT NULL,claimed INTEGER NOT NULL DEFAULT 0,UNIQUE(user_id,started));
  CREATE TABLE IF NOT EXISTS ledger(id INTEGER PRIMARY KEY,user_id INTEGER NOT NULL,amount INTEGER NOT NULL,kind TEXT NOT NULL,created INTEGER NOT NULL,ref INTEGER UNIQUE NOT NULL);
  CREATE TABLE IF NOT EXISTS day_pool(day TEXT PRIMARY KEY,active INTEGER NOT NULL DEFAULT 0,issued INTEGER NOT NULL DEFAULT 0);
  CREATE TABLE IF NOT EXISTS auth_attempts(id INTEGER PRIMARY KEY,ip TEXT NOT NULL,kind TEXT NOT NULL,created INTEGER NOT NULL);
  CREATE INDEX IF NOT EXISTS idx_auth_attempts ON auth_attempts(ip,kind,created);
  CREATE TABLE IF NOT EXISTS referral_codes(user_id INTEGER PRIMARY KEY REFERENCES users(id),code TEXT NOT NULL UNIQUE);
  CREATE TABLE IF NOT EXISTS referrals(invited_id INTEGER PRIMARY KEY REFERENCES users(id),inviter_id INTEGER NOT NULL REFERENCES users(id),created INTEGER NOT NULL,CHECK(invited_id != inviter_id));
  CREATE INDEX IF NOT EXISTS idx_referrals_inviter ON referrals(inviter_id);""")

def pwd_hash(password):
 salt=secrets.token_bytes(16)
 return base64.b64encode(salt).decode()+':'+hashlib.pbkdf2_hmac('sha256',password.encode(),salt,250000).hex()

def pwd_verify(password,stored):
 try:
  salt,digest=stored.split(':')
  return hmac.compare_digest(hashlib.pbkdf2_hmac('sha256',password.encode(),base64.b64decode(salt),250000).hex(),digest)
 except Exception:return False

def ensure_referral_code(c,uid):
 row=c.execute('SELECT code FROM referral_codes WHERE user_id=?',(uid,)).fetchone()
 if row:return row[0]
 for _ in range(5):
  code=secrets.token_hex(5).upper()
  try:
   c.execute('INSERT INTO referral_codes(user_id,code) VALUES(?,?)',(uid,code))
   return code
  except sqlite3.IntegrityError:
   row=c.execute('SELECT code FROM referral_codes WHERE user_id=?',(uid,)).fetchone()
   if row:return row[0]
 raise RuntimeError('Não foi possível gerar código de indicação')

def day(ts):return datetime.fromtimestamp(ts,timezone.utc).strftime('%Y-%m-%d')

def start(c,uid,now):
 existing=c.execute('SELECT id,ends,claimed FROM mining WHERE user_id=? ORDER BY id DESC LIMIT 1',(uid,)).fetchone()
 if existing and now<existing[1]:return {'error':'Sessão ativa','ends':existing[1]},409
 if existing and not existing[2]:return {'error':'Resgate a sessão anterior antes de iniciar outra'},409
 c.execute('INSERT INTO mining(user_id,started,ends) VALUES(?,?,?)',(uid,now,now+SESSION))
 return {'message':'Mineração iniciada','ends':now+SESSION},200

def claim(c,uid,now):
 row=c.execute('SELECT id,ends,claimed FROM mining WHERE user_id=? ORDER BY id DESC LIMIT 1',(uid,)).fetchone()
 if not row:return {'error':'Inicie uma sessão'},400
 mid,ends,claimed=row
 if claimed:return {'error':'Recompensa já resgatada'},409
 if now<ends:return {'error':'Sessão ainda não terminou','ends':ends},409
 d=day(ends)
 c.execute('INSERT OR IGNORE INTO day_pool(day) VALUES(?)',(d,))
 issued=c.execute('SELECT issued FROM day_pool WHERE day=?',(d,)).fetchone()[0]
 total=c.execute('SELECT COALESCE(SUM(amount),0) FROM ledger').fetchone()[0]
 amount=min(2_400000,DAILY_POOL-issued,MAX_SUPPLY-total)
 if amount<=0:return {'error':'Limite de emissão diária atingido'},409
 c.execute('UPDATE day_pool SET issued=issued+? WHERE day=?',(amount,d))
 c.execute('INSERT INTO ledger(user_id,amount,kind,created,ref) VALUES(?,?,?,?,?)',(uid,amount,'mining',now,mid))
 c.execute('UPDATE mining SET claimed=1 WHERE id=?',(mid,))
 return {'claimed_micro':amount,'claimed':amount/1e6},200

class Handler(BaseHTTPRequestHandler):
 def send(self,data,status=200):
  raw=json.dumps(data,ensure_ascii=False).encode()
  self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'");self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
 def do_GET(self):
  path=urlparse(self.path).path
  if path=='/':
   raw=(ROOT/'static'/'index.html').read_bytes();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);return
  if path in ('/app.js','/style.css'):
   raw=(ROOT/'static'/path.lstrip('/')).read_bytes();self.send_response(200);self.send_header('Content-Type','text/javascript' if path.endswith('js') else 'text/css');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);return
  if path=='/api/referrals':
   uid=self.auth()
   if not uid:return self.send({'error':'Não autorizado'},401)
   with conn() as c:
    code=ensure_referral_code(c,uid)
    count=c.execute('SELECT COUNT(*) FROM referrals WHERE inviter_id=?',(uid,)).fetchone()[0]
   return self.send({'code':code,'invited_count':count,'reward_enabled':False})
  if path=='/api/status':
   uid=self.auth()
   if not uid:return self.send({'error':'Não autorizado'},401)
   with conn() as c:
    balance=c.execute('SELECT COALESCE(SUM(amount),0) FROM ledger WHERE user_id=?',(uid,)).fetchone()[0]
    last=c.execute('SELECT ends,claimed FROM mining WHERE user_id=? ORDER BY id DESC LIMIT 1',(uid,)).fetchone()
    history=c.execute('SELECT amount,kind,created FROM ledger WHERE user_id=? ORDER BY id DESC LIMIT 20',(uid,)).fetchall()
   return self.send({'balance':balance/1e6,'session':{'ends':last[0],'claimed':bool(last[1])} if last else None,'history':[{'amount':r[0]/1e6,'kind':r[1],'created':r[2]} for r in history]})
  self.send({'error':'Não encontrado'},404)
 def auth(self):
  header=self.headers.get('Authorization','')
  if not header.startswith('Bearer '):return None
  token=hashlib.sha256(header[7:].encode()).hexdigest()
  with conn() as c:
   row=c.execute('SELECT user_id FROM sessions WHERE token_hash=? AND expires>?',(token,int(time.time()))).fetchone()
  return row[0] if row else None
 def do_POST(self):
  try: length=int(self.headers.get('Content-Length','-1'))
  except ValueError:return self.send({'error':'Comprimento inválido'},400)
  if length<0:return self.send({'error':'Content-Length obrigatório'},411)
  if length>4096:return self.send({'error':'Payload muito grande'},413)
  try:data=json.loads(self.rfile.read(length))
  except Exception:return self.send({'error':'JSON inválido'},400)
  path=urlparse(self.path).path;now=int(time.time())
  if path in ('/api/register','/api/login'):
   ip=self.client_address[0]
   kind='register' if path.endswith('register') else 'login'
   if not auth_attempt_allowed(ip,kind,now):return self.send({'error':'Muitas tentativas. Aguarde 15 minutos.'},429)
   if kind=='register':record_auth_attempt(ip,kind,now)
   email=str(data.get('email','')).strip().lower();password=str(data.get('password',''))
   if not 5<=len(email)<=254 or '@' not in email or not 10<=len(password)<=128:return self.send({'error':'E-mail inválido ou senha com menos de 10 caracteres'},400)
   with conn() as c:
    if path.endswith('register'):
     referral=str(data.get('referral','')).strip().upper()
     inviter=None
     if referral:
      refrow=c.execute('SELECT user_id FROM referral_codes WHERE code=?',(referral,)).fetchone()
      if not refrow:return self.send({'error':'Código de indicação inválido'},400)
      inviter=refrow[0]
     try:
      c.execute('BEGIN IMMEDIATE')
      cursor=c.execute('INSERT INTO users(email,password,created) VALUES(?,?,?)',(email,pwd_hash(password),now))
      ensure_referral_code(c,cursor.lastrowid)
      if inviter is not None:c.execute('INSERT INTO referrals(invited_id,inviter_id,created) VALUES(?,?,?)',(cursor.lastrowid,inviter,now))
      c.execute('COMMIT')
     except sqlite3.IntegrityError:
      c.execute('ROLLBACK')
      record_auth_attempt(ip,'login',now)
      return self.send({'error':'Cadastro indisponível para este e-mail'},409)
    row=c.execute('SELECT id,password FROM users WHERE email=?',(email,)).fetchone()
    if not row or not pwd_verify(password,row[1]):
     record_login_failure(ip,now)
     return self.send({'error':'Credenciais inválidas'},401)
    token=secrets.token_urlsafe(32)
    c.execute('INSERT INTO sessions VALUES(?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),row[0],now+7*86400))
   return self.send({'token':token,'expires':now+7*86400})
  uid=self.auth()
  if not uid:return self.send({'error':'Não autorizado'},401)
  if path=='/api/logout':
   token=hashlib.sha256(self.headers['Authorization'][7:].encode()).hexdigest()
   with conn() as c:c.execute('DELETE FROM sessions WHERE token_hash=?',(token,))
   return self.send({'ok':True})
  if path in ('/api/start','/api/claim'):
   with conn() as c:
    try:
     c.execute('BEGIN IMMEDIATE')
     result,status=(start(c,uid,now) if path.endswith('start') else claim(c,uid,now))
     if status!=200:c.execute('ROLLBACK')
     else:c.execute('COMMIT')
    except Exception:
     c.execute('ROLLBACK');raise
   return self.send(result,status)
  self.send({'error':'Não encontrado'},404)

if __name__=='__main__':
 init();port=int(os.getenv('PORT','8000'));print(f'PCN local: http://127.0.0.1:{port}');ThreadingHTTPServer(('0.0.0.0',port),Handler).serve_forever()
