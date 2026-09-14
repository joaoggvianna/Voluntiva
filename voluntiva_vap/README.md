# VAP — Implementação do protocolo do Voluntiva

Este pacote contém uma implementação funcional do VAP 1.0.

## Requisitos

```text
Python 3.11+
pytest
```

## Estrutura

```text
protocol/
├── auth.py
├── client.py
├── config.py
├── errors.py
├── framing.py
├── handlers.py
├── models.py
├── server.py
└── services.py

tests/
├── test_framing.py
└── test_handlers.py

docs/
└── VAP.md
```

## Rodar servidor

Na raiz:

```bash
python -m protocol.server
```

Servidor:

```text
127.0.0.1:5050
```

## Rodar cliente

Em outro terminal:

```bash
python -m protocol.client
```

Fluxo executado:

```text
PING
AUTH
LIST_ACTIONS
REGISTER_ACTION
```

## Rodar testes

```bash
pytest -v
```

## Tokens mock

Somente para desenvolvimento:

```text
token-volunteer
token-ong
token-admin
```

Antes da integração real, substituir `verify_access_token()` por validação do Supabase Auth.

## TLS

Por padrão:

```text
VAP_USE_TLS=false
```

Para habilitar:

```text
VAP_USE_TLS=true
VAP_CERTFILE=/caminho/cert.pem
VAP_KEYFILE=/caminho/key.pem
```

O cliente atualmente desativa a validação do certificado quando TLS está ativo, apenas para facilitar testes com certificado self-signed. Isso deve ser alterado em produção.
