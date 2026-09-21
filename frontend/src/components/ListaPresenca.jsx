import { Check, Users, X } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { EstadoVazio } from "@/components/EstadoVazio"
import { useApp } from "@/contexto/AppContexto"
import { listarInscritos, registrarPresenca } from "@/lib/servico"
import { hojeIso } from "@/lib/utils"

export function ListaPresenca({ acao, ongId }) {
  const { executar } = useApp()
  const inscritos = listarInscritos(acao.id)
  const liberada = acao.data <= hojeIso() && acao.situacao !== "cancelada"
  const presentes = inscritos.filter((i) => i.presenca === "presente").length
  const ausentes = inscritos.filter((i) => i.presenca === "ausente").length

  function marcar(inscricao, valor) {
    const novo = inscricao.presenca === valor ? null : valor
    executar(() => registrarPresenca(inscricao.id, ongId, novo))
  }

  if (inscritos.length === 0) {
    return (
      <EstadoVazio
        icone={Users}
        titulo="Nenhum voluntário inscrito"
        descricao="Assim que alguém se inscrever nesta ação, aparecerá aqui."
      />
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <Badge variant="secondary">{inscritos.length} inscritos</Badge>
        <Badge>{presentes} presentes</Badge>
        <Badge variant="outline">{ausentes} ausentes</Badge>
        {!liberada && (
          <span className="text-muted-foreground">
            O registro de presença é liberado na data da ação.
          </span>
        )}
      </div>

      <ul className="divide-y rounded-lg border">
        {inscritos.map((inscricao) => (
          <li
            key={inscricao.id}
            className="flex flex-wrap items-center justify-between gap-3 p-4"
          >
            <div className="min-w-0">
              <p className="font-medium">{inscricao.voluntario.nome}</p>
              <p className="truncate text-sm text-muted-foreground">
                {inscricao.voluntario.email}
                {inscricao.voluntario.telefone && ` · ${inscricao.voluntario.telefone}`}
              </p>
            </div>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant={inscricao.presenca === "presente" ? "default" : "outline"}
                disabled={!liberada}
                aria-pressed={inscricao.presenca === "presente"}
                onClick={() => marcar(inscricao, "presente")}
              >
                <Check /> Presente
              </Button>
              <Button
                size="sm"
                variant={inscricao.presenca === "ausente" ? "destructive" : "outline"}
                disabled={!liberada}
                aria-pressed={inscricao.presenca === "ausente"}
                onClick={() => marcar(inscricao, "ausente")}
              >
                <X /> Ausente
              </Button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
