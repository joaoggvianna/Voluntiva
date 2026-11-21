# Frontend — Voluntiva

Interface web do Voluntiva. React + Vite + Tailwind CSS, com os
componentes de base vindos do shadcn/ui (`src/components/ui/`).

## Como a interface fala com o backend

Todas as telas usam a API real (`backend/app/api/v1`); não há mais mock
nem dados-semente no navegador.

| Arquivo | Papel |
| --- | --- |
| `src/lib/api.ts` | cliente REST (`/api/v1`): único ponto que faz `fetch`, guarda os tokens e renova a sessão com o refresh token quando recebe 401 |
| `src/lib/ws.ts` | canal `/ws/notificacoes`, com reconexão exponencial |
| `src/lib/adaptadores.js` | converte o formato da API (snake_case, datas ISO, enums) para o que as telas exibem, e o caminho inverso nos formulários |
| `src/lib/dominio.js` | vocabulário fixo: causas, UFs, dias da semana e turnos |
| `src/lib/useCarregar.js` | hook de carga assíncrona que descarta respostas fora de ordem |
| `src/contexto/AppContexto.jsx` | sessão, perfil do usuário, catálogo de habilidades e notificações em tempo real |
| `src/types/index.ts` | tipos espelhando os schemas Pydantic do backend |

Depois de cada alteração bem-sucedida (`executar` do contexto), o contador
`versao` muda e as telas que dependem dele recarregam os dados. Uma
notificação recebida pelo WebSocket faz o mesmo.

Disponibilidade: a tela trabalha com dias e turnos (Manhã 6h–12h, Tarde
12h–18h, Noite 18h–24h). Turnos vizinhos viram uma janela só no backend
(Manhã + Tarde = 6h–18h), para uma ação das 10h às 14h casar com quem
marcou os dois.

## Como executar

```bash
npm ci
cp .env.example .env.local
npm run dev     # http://localhost:5173 (backend em http://localhost:8000)
```

O `vite.config.js` faz proxy de `/api` e `/ws` para o backend, então não
há CORS em desenvolvimento. Em produção (imagem Docker), o nginx faz o
mesmo papel (`nginx.conf`). Para subir tudo junto, use o
`docker-compose.yml` da raiz (ver `docs/GUIA_EXECUCAO.md`).

Outros comandos:

```bash
npm run build      # gera dist/
npm run lint       # eslint nos .js/.jsx
npm run typecheck  # tsc nos arquivos .ts
```

Em `npm run dev`, a tela de login mostra atalhos para as contas do seed de
desenvolvimento (senha `voluntiva123`). No build de produção eles não
aparecem.

## Divergências registradas

Dois pontos em que o frontend não bate com a stack e a identidade visual planejadas.
Nenhum dos dois é acidente de integração — os dois são decisão pendente
da equipe:

1. **JavaScript em vez de TypeScript, Tailwind 3 em vez de 4,
   React 18 em vez de 19.** A UI foi construída assim e funciona; migrar
   ~5.400 linhas de JSX é trabalho à parte. Os componentes do shadcn/ui
   também estão gerados para Tailwind 3 (`tailwind.config.js` +
   `postcss.config.js`), que o Tailwind 4 substitui pelo bloco `@theme`.

2. **A paleta não é a do README.** O README define azul petróleo
   (`#1F5F63`) + coral (`#F27A5A`); `src/index.css` usa um verde
   esmeralda (`--primary: 160 84% 32%`). Trocar é mexer em variável CSS,
   mas é decisão de UX — não foi alterado aqui.
