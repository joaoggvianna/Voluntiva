import { Link } from "react-router-dom"
import { Clock, MapPin, Sparkles, Users } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { SeloCausa } from "@/components/SeloCausa"
import { useApp } from "@/contexto/AppContexto"
import { calcularCompatibilidade, rotuloCompatibilidade } from "@/lib/compatibilidade"
import { formatarDataCurta } from "@/lib/utils"

function SituacaoAcao({ acao }) {
  if (acao.situacao === "cancelada") return <Badge variant="destructive">Cancelada</Badge>
  if (acao.situacao === "concluida") return <Badge variant="secondary">Encerrada</Badge>
  if (acao.vagasRestantes === 0) return <Badge variant="outline">Lotada</Badge>
  return null
}

export function CartaoAcao({ acao }) {
  const { usuario } = useApp()
  const { dia, mes } = formatarDataCurta(acao.data)
  const rotulo =
    acao.situacao === "ativa"
      ? rotuloCompatibilidade(calcularCompatibilidade(acao, usuario))
      : null

  return (
    <Link to={`/acoes/${acao.id}`} className="group block h-full">
      <Card className="h-full transition-colors group-hover:border-primary">
        <CardContent className="flex h-full gap-4 pt-6">
          <div className="flex h-16 w-14 shrink-0 flex-col items-center justify-center rounded-lg bg-primary/10 text-primary">
            <span className="text-2xl font-bold leading-none">{dia}</span>
            <span className="mt-1 text-xs font-semibold">{mes}</span>
          </div>
          <div className="flex min-w-0 flex-1 flex-col gap-3">
            <div className="flex flex-wrap items-center gap-2">
              <SeloCausa causa={acao.causa} />
              <SituacaoAcao acao={acao} />
              {rotulo && (
                <Badge className="gap-1">
                  <Sparkles className="h-3 w-3" />
                  {rotulo}
                </Badge>
              )}
            </div>
            <div>
              <h3 className="font-semibold leading-snug group-hover:text-primary">
                {acao.titulo}
              </h3>
              <p className="mt-1 text-sm text-muted-foreground">{acao.ong?.nome}</p>
            </div>
            <p className="line-clamp-2 text-sm text-muted-foreground">{acao.descricao}</p>
            <ul className="mt-auto space-y-1 text-xs text-muted-foreground">
              <li className="flex items-center gap-1.5">
                <MapPin className="h-3.5 w-3.5 shrink-0" />
                {acao.unidade?.cidade}/{acao.unidade?.uf}
              </li>
              <li className="flex items-center gap-1.5">
                <Clock className="h-3.5 w-3.5 shrink-0" />
                {acao.horario}
              </li>
              <li className="flex items-center gap-1.5">
                <Users className="h-3.5 w-3.5 shrink-0" />
                {acao.situacao === "ativa"
                  ? `${acao.vagasRestantes} de ${acao.vagas} vagas restantes`
                  : `${acao.inscritos} participantes`}
              </li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </Link>
  )
}
