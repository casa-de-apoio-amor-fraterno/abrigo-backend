# Usuario

Origem (Delphi — abrigo-legacy):
- Unit: `fonte/untFrmLogin.pas` (tela de login), `fonte/Unt/Usuario/`
  (`untFrmManutencaoUsuario`, `untFrmManAlterarSenha`, `untFrmConsultaUsuario`)
- Query de autenticação original:
  `SELECT id_usuario, nome, perfil FROM usuario WHERE login = :Login AND senha = :Senha`
- Banco: tabela `usuario` — colunas confirmadas via `CREATE TABLE` do dump de
  produção `sgf_abrigo` (2026-09-09): `id_usuario` (int, PK), `nome`
  (varchar(60)), `login` (varchar(60)), `senha` (varchar(60)), `ativo`
  (varchar(3) 'Sim'/'Não'), `perfil` (varchar(20)).

## Achados de segurança importantes

1. **Senha em texto plano, sem nenhum hash** (`untFrmLogin.pas`,
   `ValidaUsuario`). A coluna `senha` guarda a senha literal — confirmado nos
   dados reais do dump (ex.: senhas iguais ao login, como `'bazar'`/`'bazar'`
   ou `'cinthia'`/`'cinthia'`).
2. **A query de login nunca checa `ativo`.** Um usuário desativado
   (`ativo = 'Não'`, existe pelo menos um caso real no dump) ainda consegue
   logar no sistema legado — a coluna existe, mas não é usada na
   autenticação. **Corrigido deliberadamente no sistema novo**:
   `app/features/auth/service.py` rejeita login se `usuario.ativo` for falso.

## Estratégia de migração de senha

Não é possível (nem seria seguro) trocar a verificação para hash de um dia
para o outro — isso invalidaria a senha de todo mundo de uma vez. Em vez
disso, o schema novo já nasce com as duas colunas (`senha` e `senha_hash`,
ver `alembic/versions/0001_estrutura_inicial.py`) e no login
(`app/features/auth/service.py`):

- Se `senha_hash` já existe, valida por bcrypt.
- Se não existe, valida contra `senha` (texto plano, comportamento idêntico
  ao legado) e, se bater, **gera o hash na hora, grava em `senha_hash` e
  limpa `senha`** (lazy migration no primeiro login).

Depois que todos os usuários ativos tiverem logado ao menos uma vez no
sistema novo, uma migração futura pode dropar a coluna `senha` — só fazer
isso depois de confirmar (via `SELECT`) que não sobrou nenhum registro com
`senha_hash IS NULL AND ativo = true`.

## Tipo:
- Suporte/infraestrutura (não é uma rotina de cadastro do domínio do
  atendimento, mas afeta login)

## Status:
- Mapeado com campos reais (incluindo `ativo`, confirmado no dump). Model em
  `app/features/usuarios/models.py`. Endpoint de login usa a estratégia
  acima e bloqueia usuário inativo.
