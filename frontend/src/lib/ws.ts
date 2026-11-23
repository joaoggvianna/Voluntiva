/* ---------------------------------------------------------------------
 * Canal de notificações em tempo real (/ws/notificacoes do FastAPI).
 *
 * Usado pelo AppContexto enquanto há sessão: cada notificação gravada no
 * servidor chega aqui no mesmo formato de GET /notificacoes.
 * ------------------------------------------------------------------ */

import type { Notificacao } from '@/types'
import { BASE, normalizarOrigem, tokenStore } from './api'

function baseWebSocket(): string {
  // Sem esquema, normalizarOrigem põe https://; o replace vira wss://.
  const configurada = normalizarOrigem(import.meta.env.VITE_WS_URL).replace(/^http/i, 'ws')
  if (configurada) return configurada
  // Sem VITE_WS_URL mas com a API em outra origem (deploy no Render):
  // o WebSocket mora no mesmo host da API, só troca http(s) por ws(s).
  if (BASE) return BASE.replace(/^http/i, 'ws')
  // Mesma origem da página: em dev o Vite encaminha /ws, em produção o nginx.
  const protocolo = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${protocolo}://${window.location.host}`
}

/** Cliente do canal de notificações, com reconexão exponencial.
 *  Devolve a função que encerra a conexão. */
export function conectarNotificacoes(
  aoReceber: (n: Notificacao) => void,
): () => void {
  let socket: WebSocket | null = null
  let tentativa = 0
  let heartbeat: ReturnType<typeof setInterval> | null = null
  let reconexao: ReturnType<typeof setTimeout> | null = null
  let encerrado = false

  const conectar = () => {
    if (encerrado) return
    // Lido a cada tentativa: depois de um refresh, o token novo é usado.
    const token = tokenStore.get()
    if (!token) return

    // O token vai na primeira mensagem, não na URL: a URL do handshake
    // fica gravada no log de acesso do servidor e do proxy.
    const ws = new WebSocket(`${baseWebSocket()}/ws/notificacoes`)
    socket = ws

    // O servidor só responde 'pong' depois de aceitar o token. Sem pong a
    // tempo, a conexão é dada como morta e reaberta (com o token atual).
    // Necessário porque o proxy do Render nem sempre repassa o fechamento
    // feito pelo servidor (token recusado), e o navegador ficaria com um
    // socket aberto que nunca recebe nada.
    let prazoPong: ReturnType<typeof setTimeout> | null = null
    let finalizado = false

    // Chamado uma única vez por conexão: no fechamento normal ou quando o
    // pong não chega. Não espera o onclose, que num socket morto pode
    // demorar a disparar.
    const finalizar = () => {
      if (finalizado) return
      finalizado = true
      if (heartbeat) clearInterval(heartbeat)
      if (prazoPong) clearTimeout(prazoPong)
      if (encerrado || socket !== ws) return
      // Backoff exponencial com teto de 30s, para não martelar o servidor.
      const espera = Math.min(1000 * 2 ** tentativa++, 30_000)
      reconexao = setTimeout(conectar, espera)
    }

    const pingar = () => {
      if (ws.readyState !== WebSocket.OPEN) return
      ws.send('ping')
      if (!prazoPong) {
        prazoPong = setTimeout(() => {
          ws.close()
          finalizar()
        }, 10_000)
      }
    }

    ws.onopen = () => {
      ws.send(token)
      pingar()
      heartbeat = setInterval(pingar, 30_000)
    }

    ws.onmessage = (evento) => {
      if (evento.data === 'pong') {
        if (prazoPong) clearTimeout(prazoPong)
        prazoPong = null
        tentativa = 0
        return
      }
      try {
        aoReceber(JSON.parse(evento.data) as Notificacao)
      } catch {
        // Mensagem fora do formato esperado: ignora em vez de derrubar a UI.
      }
    }

    ws.onclose = finalizar
  }

  conectar()

  return () => {
    encerrado = true
    if (heartbeat) clearInterval(heartbeat)
    if (reconexao) clearTimeout(reconexao)
    socket?.close()
  }
}
