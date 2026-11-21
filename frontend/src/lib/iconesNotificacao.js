import { Bell, CheckCircle2, RefreshCw, Sparkles, UserMinus, UserPlus, XCircle } from "lucide-react"

/** Ícone por tipo de notificação (enum tipo_notificacao do banco). */
export const iconesNotificacao = {
  acao_criada: Sparkles,
  acao_atualizada: RefreshCw,
  acao_cancelada: XCircle,
  inscricao_confirmada: UserPlus,
  inscricao_cancelada: UserMinus,
  lembrete: Bell,
  presenca: CheckCircle2,
}
