# Operação de testes — NÃO publicar como serviço público

## Ambiente local
Python 3.11+ e sem dependências externas:

```bash
PCN_PRIVATE_BETA=0 python server.py
python -m unittest discover -s tests -v
```

O servidor local usa SQLite. A configuração `PCN_PRIVATE_BETA=1` é o padrão: bloqueia novos cadastros até que um operador conscientemente habilite a opção. **Não use `PCN_PRIVATE_BETA=0` em hospedagem pública** nesta fase.

Para habilitar painel ADM, configure `PCN_ADMIN_USER_ID` apenas no ambiente do processo com o ID numérico de uma conta existente. Não configure o ID de outra pessoa. O controle atual ainda não possui MFA e não está apto para internet pública.

## Bloqueadores de lançamento
- Sem HTTPS gerenciado no servidor embutido, proteção distribuída, autenticação reforçada e verificações de e-mail.
- Sem backups, restauração, observabilidade, limites por usuário e política antifraude suficiente.
- Sem revisão de segurança independente, testes de carga ou aprovação jurídica.

Endpoint de verificação: `GET /api/health`. Endpoint de estatísticas agregadas: `GET /api/network`.

## Backup local verificado

Para criar um backup consistente do banco SQLite em funcionamento:

```bash
python scripts/backup.py --source pcn.sqlite3
```

O script usa a API de backup do SQLite, executa `PRAGMA integrity_check` e recusa sobrescrever arquivos existentes. Os arquivos `.sqlite3` são ignorados pelo Git. **Um backup não é estratégia completa de recuperação:** testar restauração, retenção, criptografia e armazenamento externo antes de produção.
