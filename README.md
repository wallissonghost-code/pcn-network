# PCN — Crypto Network (MVP experimental)

Protótipo local, **sem criptomoeda real**, sem valor monetário e sem transações em blockchain. O botão de mineração representa uma sessão de participação, não mineração por CPU.

## Executar

Requer Python 3.10+ (somente biblioteca padrão):

```bash
python server.py
```

Abra `http://localhost:8000` no navegador. Para executar testes:

```bash
python -m unittest discover -s tests -v
```

## Recursos

Registro e login com PBKDF2, token de sessão armazenado como hash em SQLite; sessão de 24 horas, resgate único e ledger em micro-PCN; limite diário global de 24.000 PCN e oferta máxima simulada de 100 milhões; interface web responsiva.

## Limitações — NÃO publicar como serviço aberto

Sem rate limiting, verificação de e-mail, MFA, CAPTCHA, antifraude, recuperação de senha, auditoria independente ou deploy. Token no sessionStorage; SQLite e HTTP simples somente para testes. A distribuição fixa de 2,4 PCN pode esgotar o orçamento diário. Não há token on-chain, carteira externa, KYC, indicações ou painel ADM. Não depositar dinheiro ou criptomoedas.

## Próximos passos

Revisar tokenomics, criar backend de produção, implementar antifraude, RBAC, indicações e observabilidade; testes de segurança e carga; revisão jurídica e contratos em testnet.

Oferta proposta e não vinculante: 100 milhões de PCN (70% comunidade, 15% ecossistema, 10% liquidez, 5% equipe).