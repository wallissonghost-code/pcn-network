# Status — PCN Crypto Network

## Implementado
- Protótipo web e API Python local
- Cadastro e login, sessões e ledger SQLite
- Sessão diária de 24h, resgate único, teto de emissão diário e global experimental
- Testes automatizados via GitHub Actions

## Não implementado
- Hospedagem pública e banco de produção
- Antifraude, recuperação de senha, verificação de e-mail, proteção contra abuso e MFA
- Indicações, painel administrativo, Android nativo, token real e auditoria

## Segurança
**Não usar em produção.** Sem depósitos, venda ou promessa de retorno. Revisão de segurança, jurídica e tokenomics necessária antes de qualquer lançamento.

## Atualização V0.3
- Adicionado bloqueio experimental de tentativas de autenticação por IP (8 falhas/15 minutos) e teste automatizado.
- **Limitação:** bloqueio em memória, reiniciado com o servidor e não compartilhado entre instâncias. Não é adequado para produção; migrar para Redis ou gateway de rate limiting e incluir proteção de cadastro.
- Testes no GitHub Actions ainda dependem de confirmação de execução; não afirmar aprovação sem logs.
