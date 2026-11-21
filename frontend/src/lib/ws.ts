/* ---------------------------------------------------------------------
 * Canal de notificações em tempo real (/ws/notificacoes do FastAPI).
 *
 * Usado pelo AppContexto enquanto há sessão: cada notificação gravada no
 * servidor chega aqui no mesmo formato de GET /notificacoes.
 * ------------------------------------------------------------------ */

import type { Notificacao } from '@/types'
import { tokenStore } from './api'

function baseWebSocket(): string {
  const configurada = import.meta.env.VITE_WS_URL
  if (configurada) return configurada
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

    socket = new WebSocket(`${baseWebSocket()}/ws/notificacoes?token=${encodeURIComponent(token)}`)

    socket.onopen = () => {
      tentativa = 0
      heartbeat = setInterval(() => socket?.send('ping'), 30_000)
    }

    socket.onmessage = (evento) => {
      if (evento.data === 'pong') return
      try {
        aoReceber(JSON.parse(evento.data) as Notificacao)
      } catch {
        // Mensagem fora do formato esperado: ignora em vez de derrubar a UI.
      }
    }

    socket.onclose = () => {
      if (heartbeat) clearInterval(heartbeat)
      if (encerrado) return
      // Backoff exponencial com teto de 30s, para não martelar o servidor.
      const espera = Math.min(1000 * 2 ** tentativa++, 30_000)
      reconexao = setTimeout(conectar, espera)
    }
  }

  conectar()

  return () => {
    encerrado = true
    if (heartbeat) clearInterval(heartbeat)
    if (reconexao) clearTimeout(reconexao)
    socket?.close()
  }
}
