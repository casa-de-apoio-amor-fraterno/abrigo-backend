# Pessoa

Origem (Delphi — abrigo-legacy):
- Unit: `fonte/Unt/Pessoa/` (`untFrmManutencaoPessoa`, `untDtmManutencaoPessoa`,
  `untFrmConsultaPessoa`, `untDtmConsultaPessoa`)
- Telas relacionadas: avaliação social (`untFrmManutencaoAvaliacaoSocial`),
  composição familiar (`untFrmManutencaoComposicaoFamiliar`), relatório
  (`untFrmRelatorioPessoa`)
- Banco: tabela `pessoa` (ver `banco_dados_modelo/bd.mwb` e
  `Scripts/.../Add coluna tipo pessoa na tabela estadia.sql`)

Tipo:
- Cadastro (+ sub-rotinas de avaliação social e composição familiar, que devem
  ficar restritas ao perfil de assistente social conforme anotado em
  `abrigo-legacy/CasaApoio.txt`)

Dependências a analisar antes de migrar por completo:
- Vínculo com `Estadia` (tipo de pessoa: paciente/acompanhante/empréstimo)
- Vínculo com `Emprestimo` (pessoa como tomadora de item emprestado)
- Regras de acesso: avaliação social e composição familiar só para
  assistente social (regra de negócio ainda não implementada no legado)

Status:
- Mapeado (schema inicial simplificado: nome, cpf, telefone, ativo — os
  campos completos precisam ser extraídos de `untDtmManutencaoPessoa.pas` e
  da tabela `pessoa` do banco de origem)
