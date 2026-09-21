# Revis?o de seguran?a do VAP de desenvolvimento

Esta implementa??o continua usando tokens mock p?blicos e armazenamento em mem?ria.
N?o est? pronta para produ??o nem para exposi??o a redes n?o confi?veis. Mantenha
VAP_HOST=127.0.0.1 durante a valida??o. A configura??o TLS existente foi preservada:
o cliente de desenvolvimento ainda desativa a verifica??o do certificado quando TLS
? habilitado. Isso n?o autentica o servidor e n?o protege contra intermedi?rios ativos.

## Prote??es implementadas

- Cabe?alho limitado a 8192 bytes; corpo limitado por VAP_MAX_MESSAGE_SIZE (65536).
- CONTENT-LENGTH obrigat?rio, decimal sem sinal; cabe?alhos duplicados rejeitados.
- Identificadores de 1 a 128 caracteres ASCII seguros; comandos de at? 64 letras/underscores.
  IDs curtos existentes continuam aceitos, embora a especifica??o recomende UUID.
- JSON exige objeto, chaves ?nicas, n?meros finitos, Unicode v?lido e profundidade de at? 32.
- Erros de framing encerram a conex?o, impedindo reinterpretar o corpo como outro comando.
- Prazo absoluto para autentica??o, inclusive com PING, e para leitura da mensagem completa.
- Limites de conex?es, requisi??es e tentativas de autentica??o; escritas com timeout.
- AUTH inv?lido remove a identidade anterior; action_id exige inteiro positivo, sem booleanos.
- Registro/cancelamento mock protegidos por lock para tornar as opera??es at?micas no processo.
- Cliente limita respostas, detecta EOF e confere REQUEST-ID para suas requisi??es.
- Sockets s?o fechados em falhas de handshake; Windows usa bind exclusivo.

## Par?metros adicionais

| Vari?vel | Padr?o |
| --- | --- |
| VAP_MESSAGE_TIMEOUT | 30 segundos |
| VAP_WRITE_TIMEOUT | 5 segundos |
| VAP_MAX_CONNECTIONS | 64 |
| VAP_MAX_CONNECTIONS_PER_IP | 8 |
| VAP_MAX_REQUESTS_PER_CONNECTION | 1000 |
| VAP_MAX_REQUESTS_PER_SECOND | 50 por conex?o, janela de 1 segundo |
| VAP_MAX_AUTH_FAILURES | 3 por conex?o |

O prazo de leitura ? o menor entre o limite de mensagem e o limite aplic?vel ? sess?o.
Em erros de framing, a resposta de erro ? enviada em melhor esfor?o: o sistema
operacional pode entregar um reset se houver dados n?o lidos.
Conex?es excedentes s?o fechadas sem criar threads. Excesso de frequ?ncia retorna
400 BAD_REQUEST e fecha a conex?o; atingir o total de requisi??es tamb?m fecha.
O cliente deve reconectar ap?s o encerramento. Os c?digos e comandos VAP n?o mudaram.

## Limites e trabalho de produ??o ainda pendente

Limites locais reduzem consumo de recursos, mas n?o garantem prote??o contra DoS/DDoS;
reconectar reinicia os contadores por conex?o. Antes de exposi??o externa, s?o necess?rios
autentica??o real com valida??o de assinatura/emissor/audi?ncia/expira??o, TLS com
verifica??o de certificado e hostname, segredos fora do c?digo, limites globais por
identidade/IP na infraestrutura e transa??es/constraints no banco real. O lock s? protege
este processo e n?o substitui transa??es. N?o h? prote??o persistente contra replay.
A revis?o e os testes de regress?o n?o s?o auditoria independente nem garantia de aus?ncia
de vulnerabilidades. N?o foram feitas mudan?as na configura??o TLS de produ??o.

Refer?ncias t?cnicas consultadas:
- https://docs.python.org/3/library/json.html
- https://docs.python.org/3/library/ssl.html
