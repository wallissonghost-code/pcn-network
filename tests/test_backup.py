import sqlite3
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.backup import backup


class BackupTests(unittest.TestCase):
 def test_backup_preserves_rows(self):
  with tempfile.TemporaryDirectory() as tmp:
   source = Path(tmp) / 'source.sqlite3'
   target = Path(tmp) / 'backups' / 'copy.sqlite3'
   with sqlite3.connect(source) as db:
    db.execute('CREATE TABLE example(id INTEGER PRIMARY KEY, value TEXT)')
    db.execute('INSERT INTO example(value) VALUES (?)', ('preserved',))
   backup(source, target)
   with sqlite3.connect(target) as db:
    self.assertEqual(db.execute('SELECT value FROM example').fetchone()[0], 'preserved')
   with self.assertRaises(FileExistsError):
    backup(source, target)

 def test_missing_source(self):
  with tempfile.TemporaryDirectory() as tmp:
   with self.assertRaises(FileNotFoundError):
    backup(Path(tmp) / 'missing.sqlite3', Path(tmp) / 'copy.sqlite3')


if __name__ == '__main__':
 unittest.main()
