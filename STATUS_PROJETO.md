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

## Atualização V0.4
- Limitação de tentativas de login agora persistida no SQLite, sobrevivendo a reinicializações do processo.
- Limite de 4 tentativas de cadastro por IP em 15 minutos e 8 falhas de login por IP em 15 minutos.
- Testes automatizados atualizados para verificar limites de login e cadastro.
- Validação de Content-Length antes da leitura de requisições POST.
- **Não pronto para produção:** limitação por IP pode afetar redes compartilhadas; falta proteção distribuída, e-mail verificado, recuperação de conta, observabilidade e auditoria.
- Execução dos testes no GitHub Actions ainda não verificada nesta atualização.
