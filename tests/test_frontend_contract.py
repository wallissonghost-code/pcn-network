import unittest
from pathlib import Path


class FrontendContract(unittest.TestCase):
 def test_required_elements_exist(self):
  root = Path(__file__).resolve().parents[1] / 'static'
  html = (root / 'index.html').read_text(encoding='utf-8')
  for element in ('network','auth','dashboard','balance','session','history','referrals','admin','admin-stats','message','login','register','start','claim','logout','copy-referral'):
   self.assertIn('id="'+element+'"', html)

 def test_optional_api_errors_do_not_clear_session(self):
  js = (Path(__file__).resolve().parents[1] / 'static' / 'app.js').read_text(encoding='utf-8')
  self.assertIn('if(e.status===401)', js)
  self.assertIn('Indicações temporariamente indisponíveis', js)
  self.assertIn('Estatísticas administrativas temporariamente indisponíveis', js)


if __name__ == '__main__':
 unittest.main()
