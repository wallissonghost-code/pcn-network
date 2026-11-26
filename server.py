import base64, hashlib, hmac, json, os, secrets, sqlite3, time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).parent
DB=Path(os.getenv('PCN_DB',str(ROOT/'pcn.sqlite3')))
SESSION=24*3600
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
  CREATE TABLE IF NOT EXISTS day_pool(day TEXT PRIMARY KEY,active INTEGER NOT NULL DEFAULT 0,issued INTEGER NOT NULL DEFAULT 0);""")

def pwd_hash(password):
 salt=secrets.token_bytes(16)
 return base64.b64encode(salt).decode()+':'+hashlib.pbkdf2_hmac('sha256',password.encode(),salt,250000).hex()

def pwd_verify(password,stored):
 try:
  salt,digest=stored.split(':')
  return hmac.compare_digest(hashlib.pbkdf2_hmac('sha256',password.encode(),base64.b64decode(salt),250000).hex(),digest)
 except Exception:return False

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
  if int(self.headers.get('Content-Length','0'))>4096:return self.send({'error':'Payload muito grande'},413)
  try:data=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))))
  except Exception:return self.send({'error':'JSON inválido'},400)
  path=urlparse(self.path).path;now=int(time.time())
  if path in ('/api/register','/api/login'):
   email=str(data.get('email','')).strip().lower();password=str(data.get('password',''))
   if not 5<=len(email)<=254 or '@' not in email or not 10<=len(password)<=128:return self.send({'error':'E-mail inválido ou senha com menos de 10 caracteres'},400)
   with conn() as c:
    if path.endswith('register'):
     try:c.execute('INSERT INTO users(email,password,created) VALUES(?,?,?)',(email,pwd_hash(password),now))
     except sqlite3.IntegrityError:return self.send({'error':'E-mail já cadastrado'},409)
    row=c.execute('SELECT id,password FROM users WHERE email=?',(email,)).fetchone()
    if not row or not pwd_verify(password,row[1]):return self.send({'error':'Credenciais inválidas'},401)
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
