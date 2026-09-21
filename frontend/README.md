# Frontend — Voluntiva

Interface web do Voluntiva. React + Vite + Tailwind CSS, com os
componentes de base vindos do shadcn/ui (`src/components/ui/`).

## Estado atual: a UI ainda roda sobre um mock

As telas **não falam com o backend** (`backend/app/`) por enquanto. Os
dados-semente ficam em `src/data/` e as alterações são gravadas no
`localStorage` do navegador, pela dupla:

- `src/lib/armazenamento.js` — persistência (leitura/gravação/sessão);
- `src/lib/servico.js` — regras de negócio simuladas.

As coleções do mock seguem o modelo relacional de `db/migrations/`:
`usuarios`, `ongs`, `unidades`, `acoes`, `inscricoes`, `notificacoes`.

A camada de integração com o backend real **já existe e está pronta para
uso**, mas nenhuma tela a importa ainda:

| Arquivo | O que é |
| --- | --- |
| `src/lib/api.ts` | cliente da API REST (`/api/v1`), com JWT |
| `src/lib/ws.ts` | canal `/ws/notificacoes`, com reconexão exponencial |
| `src/types/index.ts` | tipos espelhando os schemas Pydantic do backend |

**TODO(equipe):** migrar as chamadas de `servico.js` para `api.ts`, tela
por tela, e remover o mock ao final.

## Como executar

```bash
npm install
cp .env.example .env.local
npm run dev     # http://localhost:5173
```

O `vite.config.js` já faz proxy de `/api` para `http://localhost:8000` e
de `/ws` para o mesmo host, então não há CORS em desenvolvimento. Como
nada chama essas rotas ainda, o backend não precisa estar no ar para a
UI funcionar.

Outros comandos:

```bash
npm run build      # gera dist/
npm run lint       # eslint nos .js/.jsx
npm run typecheck  # tsc nos poucos arquivos .ts
```

## Contas de teste (mock)

| Tipo | E-mail | Senha |
| --- | --- | --- |
| Voluntário | voluntario@teste.com | 123456 |
| ONG | ong@teste.com | 123456 |

Para restaurar os dados iniciais, limpe os dados do site no navegador.

## Divergências registradas

Dois pontos em que o frontend não bate com o que o `CLAUDE.md` descreve.
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
