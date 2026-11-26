# Arquitetura e escopo do PCN

## Estado atual: protótipo experimental
- **Frontend:** HTML/CSS/JavaScript responsivo, sem framework.
- **Backend:** Python 3, HTTP padrão, autenticação via bearer token, senhas PBKDF2.
- **Persistência:** SQLite com ledger em unidades inteiras (micro-PCN).
- **Economia de teste:** sessão de 24h, resgate manual, recompensa de até 2,4 PCN, teto diário de 24.000 PCN e teto global de 100 milhões PCN. Valores ilustrativos, sujeitos a revisão.
- **Admin:** painel somente leitura autorizado no servidor por PCN_ADMIN_EMAIL.
- **Convites:** código individual, vínculo de convite, sem bônus monetário.

## Roadmap para produto público
1. Reescrever camada de dados com migrações, banco transacional gerenciado e backups restauráveis.
2. Implementar autenticação de produção (e-mail verificado, recuperação, MFA para administradores, rate limiting distribuído e proteção contra bots).
3. Construir antifraude: detecção de múltiplas contas, regras transparentes, revisão humana e direito de contestação.
4. Reprojetar emissão: reserva de recompensa, justiça entre usuários, contabilidade imutável, concorrência e auditoria.
5. Observabilidade: logs sem PII, métricas, alertas, backups, restauração e testes de carga.
6. UX: onboarding, acessibilidade, localização, PWA e notificações opcionais.
7. Governança, termos, privacidade, retenção de dados, conformidade LGPD e revisão jurídica no Brasil.
8. Somente após auditoria e decisão explícita: avaliar token on-chain, contratos testnet, custódia e política de distribuição. Não há garantia de liquidez, preço ou valorização.

## Princípios
Nunca confundir PCN simulado com criptoativo negociável. Nunca conceder ao painel ADM permissão de editar saldos diretamente. Nenhum investimento ou depósito deve ser solicitado durante os testes.
