# Build de teste pro cliente (não é produção)

Como gerar uma build pra alguém de fora da equipe técnica testar o sistema
— dentro da mesma rede local (Wi-Fi), sem precisar de hospedagem na nuvem
nem domínio. Isso **não** é a topologia de produção (só um processo,
`--reload` desligado mas ainda sem HTTPS, sem processo supervisor tipo
systemd, etc.) — é só uma forma rápida de dar pro cliente algo mais real
que o `ng serve` de desenvolvimento pra clicar.

## Por que servir tudo por uma porta só

O backend (`app/main.py`) sabe servir o build de produção do Angular
(`npm run build`) pelo mesmo processo/porta da API, se a pasta
`abrigo-frontend/dist/abrigo-frontend/browser` existir ao lado de
`abrigo-backend`. Isso significa:
- Só **uma porta** pra abrir no firewall (a da API), não duas.
- Sem CORS pra configurar — o navegador do cliente fala com a mesma
  origem pra tudo (`environment.production.ts`/`environment.ts` já usam
  `apiBaseUrl: '/api'`, relativo).
- Mais parecido com produção de verdade do que dois `ng serve`/`uvicorn
  --reload` juntos (que foi o que usamos antes pra testar no celular).

## Passo a passo

1. **Build do frontend** (gera `abrigo-frontend/dist/abrigo-frontend/browser`):

   ```bash
   cd abrigo-frontend
   npm run build
   ```

2. **Subir o backend sem `--reload`, escutando na rede** (não só
   `localhost`):

   ```bash
   cd abrigo-backend
   .venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

3. **Descobrir o IP da sua máquina na rede** (`ipconfig`, procurar o
   adaptador Wi-Fi/Ethernet ativo) e **abrir a porta 8000** no firewall do
   Windows (perfil "Rede privada", não "Pública" — ver aviso abaixo).

4. Cliente acessa, do celular/notebook dele **na mesma rede Wi-Fi**:
   `http://<seu-IP-na-rede>:8000`

## Se o frontend mudar depois de já estar rodando

O backend só lê os arquivos da pasta `dist/` quando o processo sobe — se
você alterar o frontend, precisa rodar `npm run build` de novo **e**
reiniciar o `uvicorn` (sem `--reload` ele não recarrega sozinho).

## Avisos importantes

- **Sem HTTPS**: o tráfego (login, token, dados) passa sem criptografia na
  rede local. Aceitável pra um teste rápido com gente de confiança na
  mesma rede; não é como produção vai funcionar.
- **Banco de dados real**: se o backend estiver apontando pro banco de
  dev/teste com dados migrados de produção (`abrigo_teste`, ver
  `docs/migracao-postgres.md`), o cliente vai ver dados reais de pessoas
  atendidas. Tudo bem se for alguém da própria instituição testando; tome
  cuidado se for alguém externo.
- **`JWT_SECRET_KEY`**: precisa estar definida no `.env` (≥32 caracteres) —
  a API não sobe sem isso (ver `app/core/config.py`).
- **Feche a porta no firewall depois** — enquanto aberta, qualquer
  dispositivo na mesma rede (não só o do cliente) consegue acessar.

## Quando isso deixar de ser suficiente

Pra dar acesso a alguém que **não** está na mesma rede física (cliente
remoto, ou querer deixar isso no ar por mais tempo sem depender do seu PC
ligado), o próximo passo é hospedar numa plataforma de nuvem (Render,
Fly.io, Railway...) com um Postgres gerenciado — isso já é infraestrutura
de verdade (contas, variáveis de ambiente de produção, etc.), fora do
escopo deste documento.
