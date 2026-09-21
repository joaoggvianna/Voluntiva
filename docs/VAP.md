# VAP — Voluntiva Application Protocol 1.0

## 1. Transporte

```text
VAP/1.0
sobre TLS
sobre TCP
```

Porta padrão de desenvolvimento:

```text
5050
```

Encoding:

```text
UTF-8
```

## 2. Estrutura da requisição

```text
VAP/1.0
COMMAND: <COMMAND>
REQUEST-ID: <UUID>
CONTENT-LENGTH: <bytes>

<JSON>
```

Exemplo:

```text
VAP/1.0
COMMAND: REGISTER_ACTION
REQUEST-ID: 550e8400-e29b-41d4-a716-446655440000
CONTENT-LENGTH: 16

{"action_id":15}
```

## 3. Resposta

```text
VAP/1.0 <CODE> <LABEL>
REQUEST-ID: <UUID>
CONTENT-LENGTH: <bytes>

<JSON>
```

## 4. Comandos

### PING

Não exige autenticação.

Resposta:

```json
{"message":"PONG"}
```

### AUTH

Payload:

```json
{"token":"<access_token>"}
```

Associa a identidade à conexão.

### LIST_ACTIONS

Exige autenticação.

Retorna ações disponíveis.

### REGISTER_ACTION

Exige `VOLUNTEER`.

Payload:

```json
{"action_id":15}
```

### CANCEL_REGISTRATION

Exige `VOLUNTEER`.

Payload:

```json
{"action_id":15}
```

## 5. Códigos

```text
200 OK
201 CREATED
400 BAD_REQUEST
401 UNAUTHORIZED
403 FORBIDDEN
404 NOT_FOUND
408 TIMEOUT
409 CONFLICT
413 PAYLOAD_TOO_LARGE
500 INTERNAL_ERROR
```

## 6. Segurança

- autenticação por token
- TLS em produção
- máximo padrão: 64 KB
- timeout de autenticação: 30s
- timeout de inatividade: 120s
- cliente não envia `user_id` nem `role`
- servidor deriva identidade da sessão autenticada
- erros internos não expõem stacktrace

## 7. Integração com FastAPI

O arquivo `services.py` atual é mock.

Na aplicação real ele deve ser substituído por chamadas aos mesmos services usados pela API REST.

Exemplo:

```text
REST Controller ─┐
                 ├── RegistrationService
VAP Handler ─────┘
                       ↓
                    Supabase
```

## 8. Concorrência

O servidor aceita múltiplos clientes com threads.

No ambiente real, a disputa pela última vaga deve ser resolvida no PostgreSQL com transação/locking/constraint, e não apenas pela memória do servidor.
