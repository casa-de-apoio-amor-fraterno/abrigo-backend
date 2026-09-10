# Usuario

Origem (Delphi — abrigo-legacy):
- Unit: `fonte/untFrmLogin.pas` (tela de login), `fonte/Unt/Usuario/`
  (`untFrmManutencaoUsuario`, `untFrmManAlterarSenha`, `untFrmConsultaUsuario`)
- Query de autenticação original:
  `SELECT id_usuario, nome, perfil FROM usuario WHERE login = :Login AND senha = :Senha`
- Banco: tabela `usuario` (colunas confirmadas: `id_usuario`, `login`, `senha`,
  `nome`, `perfil`)

**Achado de segurança importante:** o sistema legado compara a senha em
**texto plano**, sem nenhum hash (`untFrmLogin.pas`, `ValidaUsuario`). A
coluna `senha` no banco de produção (em uso desde 2013) guarda a senha
literal do usuário.

## Estratégia de migração adotada

Não é possível (nem seria seguro) simplesmente trocar a verificação para
hash de um dia para o outro — isso invalidaria a senha de todo mundo de uma
vez. Em vez disso:

1. Migração Alembic **aditiva**: adiciona a coluna `usuario.senha_hash`
   (nullable), sem alterar/remover `usuario.senha`.
2. No login (`app/features/auth/service.py`):
   - Se `senha_hash` já existe, valida por bcrypt.
   - Se não existe, valida contra `senha` (texto plano, comportamento
     idêntico ao legado) e, se bater, **gera o hash na hora, grava em
     `senha_hash` e limpa `senha`** (lazy migration no primeiro login).
3. Depois que todos os usuários ativos tiverem logado ao menos uma vez no
   sistema novo, uma migração futura pode dropar a coluna `senha` — só fazer
   isso depois de confirmar (via `SELECT` direto) que não sobrou nenhum
   registro com `senha_hash IS NULL AND ativo = 1`.

Tipo:
- Suporte/infraestrutura (não é uma rotina de cadastro do domínio do
  atendimento, mas afeta login)

Status:
- Mapeado. Model criado (`app/features/usuarios/models.py`) mapeando a
  tabela existente. Endpoint de login usa a estratégia acima.
