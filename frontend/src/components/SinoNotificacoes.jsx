import { Link, useNavigate } from "react-router-dom"
import { Bell } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useApp } from "@/contexto/AppContexto"
import { iconesNotificacao } from "@/lib/iconesNotificacao"
import { listarNotificacoes, marcarNotificacaoLida } from "@/lib/servico"
import { cn, formatarDataHora } from "@/lib/utils"

export function SinoNotificacoes() {
  const { usuario, executar, notificacoesNaoLidas } = useApp()
  const navegar = useNavigate()
  const recentes = listarNotificacoes(usuario.id).slice(0, 5)

  function abrir(notificacao) {
    executar(() => marcarNotificacaoLida(notificacao.id))
    navegar(`/acoes/${notificacao.acaoId}`)
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="relative" aria-label="Notificações">
          <Bell className="h-5 w-5" />
          {notificacoesNaoLidas > 0 && (
            <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[10px] font-bold text-destructive-foreground">
              {notificacoesNaoLidas}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80">
        <DropdownMenuLabel>Notificações</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {recentes.length === 0 && (
          <p className="px-2 py-6 text-center text-sm text-muted-foreground">
            Nenhuma notificação por enquanto.
          </p>
        )}
        {recentes.map((notificacao) => {
          const Icone = iconesNotificacao[notificacao.tipo] ?? Bell
          return (
            <DropdownMenuItem
              key={notificacao.id}
              className={cn(
                "flex cursor-pointer items-start gap-2 py-2",
                !notificacao.lida && "bg-accent/40"
              )}
              onSelect={() => abrir(notificacao)}
            >
              <Icone className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
              <div className="space-y-0.5">
                <p className="text-sm font-medium">{notificacao.titulo}</p>
                <p className="line-clamp-2 text-xs text-muted-foreground">
                  {notificacao.mensagem}
                </p>
                <p className="text-[11px] text-muted-foreground">
                  {formatarDataHora(notificacao.createdAt)}
                </p>
              </div>
            </DropdownMenuItem>
          )
        })}
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild className="justify-center text-primary">
          <Link to="/painel?aba=notificacoes">Ver todas</Link>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
