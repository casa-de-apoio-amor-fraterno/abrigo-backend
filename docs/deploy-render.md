# Deploy de teste no Render

Como colocar o sistema no ar de verdade (URL pública, acessível de
qualquer lugar) usando o [Render](https://render.com) (grátis) + o Postgres
já criado no [Neon](https://neon.tech). Ainda não é a topologia definitiva
de produção (free tier "dorme" depois de inatividade, sem alerta/monitoramento,
etc.) — é um passo além do "build de teste" local (`docs/build-de-teste.md`),
com URL de verdade pra dar pro cliente.

## Como funciona

Um **único serviço** no Render builda os dois repositórios juntos: o
`Dockerfile` (raiz deste repo) clona o `abrigo-frontend` numa etapa de
build separada (imagem Node), gera o build de produção do Angular, e copia
só o resultado (HTML/JS/CSS) pra dentro da imagem final do backend —
que serve tudo pela mesma porta (mesmo mecanismo que já testamos
localmente, ver `app/main.py`). Resultado: uma URL só, sem CORS pra
configurar entre frontend e backend.

## Passo a passo

### 1. Criar a conta no Render

[render.com](https://render.com) → criar conta (dá pra usar GitHub, sem
cartão pro plano free) → autorizar o Render a acessar os repositórios da
organização `casa-de-apoio-amor-fraterno` no GitHub (ou pelo menos o
`abrigo-backend`).

### 2. Criar o serviço via Blueprint

No dashboard: **New > Blueprint** → selecionar o repositório
`abrigo-backend`. O Render detecta o `render.yaml` deste repo
automaticamente e propõe criar o serviço `abrigo-backend` (Docker, plano
Free).

Na tela de confirmação, ele vai pedir pra preencher os valores marcados
`sync: false` no `render.yaml`:

- **`DATABASE_URL`**: a connection string do Neon, com o driver ajustado —
  pega a que vocês já têm e troca só o começo:
  ```
  postgresql+psycopg://neondb_owner:SENHA@ep-xxxxx.aws.neon.tech/neondb?sslmode=require&channel_binding=require
  ```
  (`postgresql://` → `postgresql+psycopg://`, resto igual).
- **`CORS_ORIGINS`**: como é um serviço só (mesma origem pro front e API),
  isso não é usado de verdade agora — bota um placeholder válido tipo
  `["https://localhost"]` por enquanto (não pode ser `["*"]`, a API recusa
  isso na inicialização — ver `app/core/config.py`). Depois do primeiro
  deploy, quando souberem a URL de verdade do serviço, voltem aqui e
  troquem pela URL real (só importa se algum dia acessarem a API de outra
  origem, ex. testando de outro app).

`JWT_SECRET_KEY` é gerada automaticamente pelo Render (`generateValue:
true` no blueprint) — não precisa preencher.

### 3. Deploy

Clicar em **Apply**/**Create**. O primeiro build demora uns minutos (clona
e builda o Angular + instala as dependências Python). Acompanhar os logs
na aba do serviço.

Quando concluir, o Render mostra a URL pública, algo como:
```
https://abrigo-backend-xxxx.onrender.com
```

Testar: abrir `https://<sua-url>/api/health` (deve responder
`{"status": "ok"}`) e depois a raiz `https://<sua-url>/` (deve abrir a
tela de login do Abrigo).

### 4. Login

Usem o usuário master já criado no banco Neon:
- login: `master`
- senha: a que foi definida quando o banco foi populado — troquem assim
  que possível pelo próprio app.

## Avisos do plano gratuito

- **"Dorme" depois de ~15 min sem uso** — a primeira requisição depois
  disso demora uns 30-50s pra "acordar" o serviço. Normal, não é erro.
- **O Neon também suspende o compute quando ocioso** — mesmo efeito, pode
  somar aos dois na primeira visita do dia.
- **`git clone` do `abrigo-frontend` sempre pega o `main` mais recente** no
  momento do build — não está fixado numa versão/tag pareada com o backend
  ainda. Bom o suficiente agora; considerar pin por tag/branch quando
  frontend e backend precisarem ser versionados juntos de verdade.
- Pra atualizar depois de um novo commit: o Render redeploya sozinho a
  cada push no `main` deste repo (auto-deploy ligado por padrão) — mas só
  reage a mudanças **neste** repositório; um commit só no `abrigo-frontend`
  não dispara redeploy automático aqui (precisaria de um "Deploy Hook" do
  Render chamado a partir de uma Action do outro repo — fora do escopo
  deste guia, considerar se isso virar fricção no dia a dia).
