"""Create a consistent offline SQLite backup of the experimental PCN database."""
import argparse
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def backup(source, destination):
 source = Path(source).resolve()
 destination = Path(destination).resolve()
 if not source.is_file():
  raise FileNotFoundError(f'Banco de origem inexistente: {source}')
 if source == destination:
  raise ValueError('O destino não pode ser igual à origem')
 if destination.exists():
  raise FileExistsError(f'O backup já existe: {destination}')
 destination.parent.mkdir(parents=True, exist_ok=True)
 try:
  with sqlite3.connect(f'file:{source}?mode=ro', uri=True) as src:
   with sqlite3.connect(destination) as dst:
    src.backup(dst)
    integrity = dst.execute('PRAGMA integrity_check').fetchone()[0]
    if integrity != 'ok':
     raise RuntimeError(f'Falha na integridade do backup: {integrity}')
 except Exception:
  destination.unlink(missing_ok=True)
  raise
 return destination


def main():
 parser = argparse.ArgumentParser(description='Backup local do PCN (simulação)')
 parser.add_argument('--source', default=os.getenv('PCN_DB', 'pcn.sqlite3'))
 parser.add_argument('--destination')
 args = parser.parse_args()
 stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
 dest = args.destination or f'backups/pcn-{stamp}.sqlite3'
 print(backup(args.source, dest))


if __name__ == '__main__':
 main()
