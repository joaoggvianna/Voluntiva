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

### CREATE_ACTION

Exige `ONG` ou `ADMIN`. A conta de ONG precisa ter vínculo com a
organização (e com a unidade, se `unit_id` for informado). Resposta
`201 CREATED`.

Payload:

```json
{
  "org_id": "<uuid, opcional se a conta gere uma única ONG; obrigatório para ADMIN>",
  "unit_id": "<uuid, opcional>",
  "title": "Mutirão na praça",
  "description": "opcional",
  "location": "opcional, ponto de encontro",
  "starts_at": "2030-05-10T09:00:00-03:00",
  "ends_at": "2030-05-10T12:00:00-03:00",
  "capacity": 20,
  "skills": ["<uuid de habilidade>"],
  "publish": true
}
```

`starts_at` e `ends_at` são ISO 8601 **com fuso**. Sem `publish: true`, a
ação nasce como rascunho (`DRAFT`). Ao publicar, voluntários compatíveis
recebem notificação.

Resposta:

```json
{"id":42,"title":"Mutirão na praça","status":"OPEN","starts_at":"...","ends_at":"...","capacity":20}
```

### UPDATE_ACTION

Exige `ONG` ou `ADMIN` com vínculo à ação. Envia só o que muda.

Payload:

```json
{"action_id":42,"capacity":25,"status":"CANCELLED"}
```

Campos aceitos: `title`, `description`, `location`, `starts_at`,
`ends_at`, `capacity`, `unit_id`, `status`.

Status aceitos: `OPEN`, `IN_PROGRESS`, `CLOSED`, `CANCELLED`, seguindo as
transições válidas (`DRAFT -> OPEN|CANCELLED`, `OPEN -> IN_PROGRESS|CLOSED|CANCELLED`,
`IN_PROGRESS -> CLOSED|CANCELLED`). `CLOSED` e `CANCELLED` são finais.
`capacity` não pode ficar abaixo das inscrições confirmadas (`409 CONFLICT`).
Mudanças de título, data/horário ou local notificam os inscritos; cancelar
também.

### CHECK_IN / CHECK_OUT

Exigem `ONG` ou `ADMIN` com vínculo à ação. Identificam o voluntário pelo
e-mail da inscrição.

Payload:

```json
{"action_id":42,"volunteer_email":"ana@exemplo.com"}
```

Resposta (`201` no check-in, `200` no check-out):

```json
{"action_id":42,"volunteer_email":"ana@exemplo.com","check_in":"...","check_out":"...","hours":3.0}
```

As horas são calculadas pelo banco (`presenca.horas_computadas`). O
check-in só é aceito a partir do dia da ação e para inscrição confirmada.

### LIST_NOTIFICATIONS

Exige autenticação (qualquer papel). Lista só as notificações do próprio
usuário.

Payload (opcional):

```json
{"unread_only":true,"limit":20}
```

Resposta:

```json
{
  "unread": 3,
  "notifications": [
    {"id":"<uuid>","type":"ACAO_CANCELADA","title":"Ação cancelada",
     "message":"...","read":false,"created_at":"...","action_id":42}
  ]
}
```

Notificações geradas por comandos VAP são gravadas no banco, mas o envio
em tempo real (WebSocket) só existe no processo da API; a interface web as
mostra na próxima carga.

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
