# PCN — Crypto Network

**Rede experimental de recompensas simuladas.** Não há criptomoeda real, blockchain, saque, depósito, cotação ou investimento. A sessão diária não utiliza mineração computacional.

## O que funciona
- Cadastro/login, senhas com PBKDF2 e sessões com tokens armazenados como hash
- Sessões de 24 horas, resgate único e histórico de saldo em micro-PCN
- Teto diário global de emissão simulada e limite máximo de oferta
- Indicações por código, **sem bônus** e sem emissão extra
- Estatísticas agregadas da rede e painel administrativo somente leitura
- Testes unitários e de integração HTTP executados no GitHub Actions

## Executar localmente
Requer Python 3.11+ e somente biblioteca padrão.

```bash
PCN_PRIVATE_BETA=0 python server.py
```

Abra http://127.0.0.1:8000. Para testes:

```bash
python -m unittest discover -s tests -v
```

Por segurança, o servidor escuta apenas em `127.0.0.1` e bloqueia novos cadastros por padrão. `PCN_PRIVATE_BETA=0` habilita cadastro **somente para desenvolvimento local**. Não exponha essa configuração na internet.

Para liberar o painel administrativo com o ID numérico de uma conta já cadastrada, defina `PCN_ADMIN_USER_ID` no ambiente do processo. Não armazene dados pessoais ou segredos no GitHub.

## API de teste
`GET /api/health`, `GET /api/network`, `POST /api/register`, `POST /api/login`, `POST /api/logout`, `GET /api/status`, `POST /api/start`, `POST /api/claim`, `GET /api/referrals`, `GET /api/admin/access`, `GET /api/admin/stats`.

## Limitações e próximos passos
**Não implantar publicamente.** Faltam verificação de e-mail, recuperação de senha, MFA administrativo, antifraude, proteção contra abuso distribuído, banco gerenciado, backups restauráveis, auditoria de segurança, testes de carga e revisão jurídica/LGPD. A política de emissão e a eventual criação de um token on-chain exigem validação separada.

Consulte [arquitetura](docs/ARQUITETURA.md) e [operação](docs/DEPLOY.md). A proposta ilustrativa de oferta é 100 milhões de PCN (70% comunidade, 15% ecossistema, 10% liquidez, 5% equipe), sem compromisso de emissão real ou valorização.
