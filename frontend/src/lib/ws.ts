/* ---------------------------------------------------------------------
 * Canal de notificações em tempo real (/ws/notificacoes do FastAPI).
 *
 * STATUS: ainda NÃO está ligado às telas — o sino de notificações
 * (src/components/SinoNotificacoes.jsx) lê do mock em src/lib/servico.js.
 * TODO(equipe): trocar o polling do mock por este cliente.
 * ------------------------------------------------------------------ */

import type { Notificacao } from '@/types'
import { tokenStore } from './api'

/** Cliente do canal de notificações, com reconexão exponencial. */
export function conectarNotificacoes(
  aoReceber: (n: Notificacao) => void,
): () => void {
  let socket: WebSocket | null = null
  let tentativa = 0
  let heartbeat: ReturnType<typeof setInterval> | null = null
  let encerrado = false

  const conectar = () => {
    if (encerrado) return
    const token = tokenStore.get()
    if (!token) return

    const base = import.meta.env.VITE_WS_URL ?? 'ws://localhost:8000'
    socket = new WebSocket(`${base}/ws/notificacoes?token=${encodeURIComponent(token)}`)

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
      setTimeout(conectar, espera)
    }
  }

  conectar()

  return () => {
    encerrado = true
    if (heartbeat) clearInterval(heartbeat)
    socket?.close()
  }
}
