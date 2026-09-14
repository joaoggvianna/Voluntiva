# Voluntiva

**Voluntiva** é um sistema de gestão de voluntários voltado a organizações não governamentais (ONGs), desenvolvido como projeto acadêmico integrando as disciplinas de **Laboratório de Projeto de Software**, **Projeto de Protocolo de Redes** e **Laboratório de Banco de Dados**.

## Objetivo

O projeto tem como objetivo centralizar e facilitar a gestão de voluntários, ações sociais e inscrições em eventos promovidos por ONGs. A plataforma deverá permitir que organizações cadastrem oportunidades de voluntariado e que voluntários encontrem ações compatíveis com seu perfil, habilidades e disponibilidade.

## Funcionalidades previstas

- Cadastro e autenticação de voluntários e ONGs;
- Cadastro de unidades e ações sociais;
- Consulta de oportunidades de voluntariado;
- Inscrição e cancelamento de participação em ações;
- Registro de habilidades e disponibilidade dos voluntários;
- Controle de presença e histórico de participação;
- Notificações sobre criação, atualização ou cancelamento de ações;
- Gestão das informações por meio de um banco de dados relacional.

## Relação com as disciplinas

### Laboratório de Projeto de Software

Responsável pela definição de requisitos, casos de uso, arquitetura da aplicação, regras de negócio, interface e organização dos módulos do sistema.

### Projeto de Protocolo de Redes

A aplicação utilizará uma arquitetura cliente-servidor. A comunicação entre clientes e servidor será feita por meio de um protocolo de aplicação próprio sobre TCP, com mensagens para operações como autenticação, consulta de eventos, inscrições, atualizações e notificações.

Exemplos de comandos previstos:

```text
LOGIN
LIST_EVENTS
JOIN_EVENT
LEAVE_EVENT
CREATE_EVENT
UPDATE_EVENT
CHECK_IN
CHECK_OUT
PING
PONG
```

### Laboratório de Banco de Dados

O banco de dados armazenará informações relacionadas a voluntários, ONGs, unidades, ações sociais, habilidades, inscrições, presença e histórico de participação.

Entidades iniciais previstas:

- Voluntário;
- ONG;
- Unidade;
- Evento/Ação Social;
- Habilidade;
- Inscrição;
- Presença;
- Usuário.

## Arquitetura inicial

```text
Cliente Voluntário ─┐
                    │
Cliente ONG ─────────┼── TCP / Protocolo Voluntiva ── Servidor ── Banco de Dados
                    │
Cliente Unidade ─────┘
```

## Identidade visual do frontend

A interface web seguirá uma identidade visual acolhedora, moderna e ligada à ideia de comunidade e impacto social.

### Paleta principal

| Uso | Cor | Hex |
| --- | --- | --- |
| Primária | Azul petróleo | `#1F5F63` |
| Secundária | Azul claro suave | `#DDEFF0` |
| Destaque | Coral | `#F27A5A` |
| Fundo | Off-white | `#F8FAF9` |
| Texto | Grafite | `#263238` |
| Bordas | Cinza claro | `#D9E2E1` |

### Cores de estado

| Estado | Hex |
| --- | --- |
| Sucesso | `#3F7D58` |
| Aviso | `#D99A35` |
| Erro | `#C94C4C` |

### Diretrizes de uso

- Aproximadamente **70% de tons neutros**, **20% de azul petróleo** e **10% de coral**;
- Azul petróleo para identidade, navegação, ícones e ações secundárias;
- Coral reservado principalmente para CTAs e ações importantes;
- Fundo majoritariamente off-white ou branco para manter leveza e legibilidade;
- Cards com bordas discretas e contraste moderado, evitando excesso de cores e gradientes;
- A interface deve transmitir confiança, proximidade e organização sem assumir uma estética corporativa excessiva.

Exemplo de variáveis CSS:

```css
:root {
  --primary: #1F5F63;
  --primary-light: #DDEFF0;
  --accent: #F27A5A;
  --background: #F8FAF9;
  --surface: #FFFFFF;
  --text: #263238;
  --text-muted: #6B7777;
  --border: #D9E2E1;
  --success: #3F7D58;
  --warning: #D99A35;
  --danger: #C94C4C;
}
```

## Equipe

- Carlos Gabriel Gouveia
- João Gabriel Guedes Vianna
- João Guilherme Costa Couto
- João Victor Pereira Bicalho
- Mateus Munhoz Guimarães

## Status

🚧 Projeto em fase inicial de planejamento e definição da arquitetura.

## Próximos passos

1. Levantamento e documentação dos requisitos;
2. Definição dos casos de uso;
3. Modelagem do banco de dados;
4. Especificação do protocolo de comunicação;
5. Definição da stack de desenvolvimento;
6. Implementação do servidor e dos clientes;
7. Integração e testes.


## Protocolo VAP implementado

O m?dulo [voluntiva_vap](voluntiva_vap/README.md) cont?m o servidor TCP, o cliente,
os testes e a especifica??o VAP/1.0. As prote??es implementadas e as limita??es
est?o em [Seguran?a do VAP](voluntiva_vap/docs/SECURITY.md).

Para executar, entre em `voluntiva_vap`, crie e ative um ambiente virtual com
Python 3.11+, instale `requirements.txt` e execute `pytest -v`. Inicie o servidor
com `python -m protocol.server` e, em outro terminal com o mesmo ambiente,
execute `python -m protocol.client`.

A implementa??o usa autentica??o e servi?os mock para valida??o local; a integra??o
com banco e autentica??o reais e a configura??o TLS de produ??o continuam pendentes.
