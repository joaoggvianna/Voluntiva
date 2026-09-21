import { Link } from "react-router-dom"
import { Bell, CheckCheck } from "lucide-react"
import { Button } from "@/components/ui/button"
import { EstadoVazio } from "@/components/EstadoVazio"
import { useApp } from "@/contexto/AppContexto"
import { iconesNotificacao } from "@/lib/iconesNotificacao"
import {
  listarNotificacoes,
  marcarNotificacaoLida,
  marcarTodasNotificacoesLidas,
} from "@/lib/servico"
import { cn, formatarDataHora } from "@/lib/utils"

export function ListaNotificacoes() {
  const { usuario, executar } = useApp()
  const notificacoes = listarNotificacoes(usuario.id)
  const naoLidas = notificacoes.filter((n) => !n.lida).length

  if (notificacoes.length === 0) {
    return (
      <EstadoVazio
        icone={Bell}
        titulo="Nenhuma notificação"
        descricao="Você será avisado sobre criação, atualização e cancelamento de ações."
      />
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {naoLidas === 0 ? "Tudo em dia." : `${naoLidas} não lidas`}
        </p>
        {naoLidas > 0 && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => executar(() => marcarTodasNotificacoesLidas(usuario.id))}
          >
            <CheckCheck /> Marcar todas como lidas
          </Button>
        )}
      </div>
      <ul className="divide-y rounded-lg border">
        {notificacoes.map((notificacao) => {
          const Icone = iconesNotificacao[notificacao.tipo] ?? Bell
          return (
            <li
              key={notificacao.id}
              className={cn("flex gap-3 p-4", !notificacao.lida && "bg-accent/40")}
            >
              <div className="mt-0.5 h-fit rounded-full bg-primary/10 p-2">
                <Icone className="h-4 w-4 text-primary" />
              </div>
              <div className="min-w-0 flex-1 space-y-1">
                <p className="text-sm font-semibold">{notificacao.titulo}</p>
                <p className="text-sm text-muted-foreground">{notificacao.mensagem}</p>
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
                  <span>{formatarDataHora(notificacao.createdAt)}</span>
                  <Link
                    to={`/acoes/${notificacao.acaoId}`}
                    className="font-medium text-primary hover:underline"
                    onClick={() => executar(() => marcarNotificacaoLida(notificacao.id))}
                  >
                    Ver ação
                  </Link>
                  {!notificacao.lida && (
                    <button
                      type="button"
                      className="hover:text-foreground"
                      onClick={() => executar(() => marcarNotificacaoLida(notificacao.id))}
                    >
                      Marcar como lida
                    </button>
                  )}
                </div>
              </div>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
