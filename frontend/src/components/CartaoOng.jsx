import { Link } from "react-router-dom"
import { CalendarDays, MapPin } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { SeloCausa } from "@/components/SeloCausa"

export function CartaoOng({ ong }) {
  const cidades = [...new Set(ong.unidades.map((u) => `${u.cidade}/${u.uf}`))]

  return (
    <Link to={`/ongs/${ong.id}`} className="group block h-full">
      <Card className="h-full transition-colors group-hover:border-primary">
        <CardContent className="flex h-full flex-col gap-3 pt-6">
          <SeloCausa causa={ong.causa} />
          <h3 className="text-lg font-semibold group-hover:text-primary">{ong.nome}</h3>
          <p className="line-clamp-3 text-sm text-muted-foreground">{ong.descricao}</p>
          <ul className="mt-auto space-y-1 text-xs text-muted-foreground">
            <li className="flex items-center gap-1.5">
              <MapPin className="h-3.5 w-3.5 shrink-0" />
              {cidades.join(", ")}
            </li>
            <li className="flex items-center gap-1.5">
              <CalendarDays className="h-3.5 w-3.5 shrink-0" />
              {ong.acoesAbertas === 1
                ? "1 ação aberta"
                : `${ong.acoesAbertas} ações abertas`}
            </li>
          </ul>
        </CardContent>
      </Card>
    </Link>
  )
}
