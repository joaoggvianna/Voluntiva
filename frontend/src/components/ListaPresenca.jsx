import { Check, LogIn, LogOut, Users } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Carregando, ErroCarga } from "@/components/Carregando"
import { EstadoVazio } from "@/components/EstadoVazio"
import { useApp } from "@/contexto/AppContexto"
import { estadoPresenca, horaLocal, paraInscrito } from "@/lib/adaptadores"
import { api } from "@/lib/api"
import { useCarregar } from "@/lib/useCarregar"
import { hojeIso } from "@/lib/utils"

/** Inscritos de uma ação e registro de presença por check-in/check-out.
 *  As horas de cada voluntário são calculadas pelo banco no check-out. */
export function ListaPresenca({ acao }) {
  const { executar, versao } = useApp()
  const { dados: inscritos, carregando, erro, recarregar } = useCarregar(
    () => api.listarInscritos(acao.id).then((lista) => lista.map(paraInscrito)),
    [acao.id, versao]
  )
  const liberada = acao.data <= hojeIso() && acao.situacao !== "cancelada"

  if (erro && !inscritos) return <ErroCarga erro={erro} aoTentarDeNovo={recarregar} />
  if (carregando && !inscritos) return <Carregando />

  if (inscritos.length === 0) {
    return (
      <EstadoVazio
        icone={Users}
        titulo="Nenhum voluntário inscrito"
        descricao="Assim que alguém se inscrever nesta ação, aparecerá aqui."
      />
    )
  }

  const presentes = inscritos.filter((i) => estadoPresenca(i) === "presente").length
  const emAndamento = inscritos.filter((i) => estadoPresenca(i) === "em_andamento").length

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <Badge variant="secondary">{inscritos.length} inscritos</Badge>
        <Badge>{presentes} com presença completa</Badge>
        {emAndamento > 0 && <Badge variant="outline">{emAndamento} sem check-out</Badge>}
        {!liberada && (
          <span className="text-muted-foreground">
            O registro de presença é liberado na data da ação.
          </span>
        )}
      </div>

      <ul className="divide-y rounded-lg border">
        {inscritos.map((inscrito) => {
          const estado = estadoPresenca(inscrito)
          return (
            <li key={inscrito.id} className="flex flex-wrap items-center justify-between gap-3 p-4">
              <div className="min-w-0">
                <p className="font-medium">{inscrito.voluntario.nome}</p>
                <p className="truncate text-sm text-muted-foreground">
                  {inscrito.voluntario.email}
                  {inscrito.voluntario.telefone && ` · ${inscrito.voluntario.telefone}`}
                </p>
                {inscrito.checkIn && (
                  <p className="text-xs text-muted-foreground">
                    Entrada {horaLocal(inscrito.checkIn)}
                    {inscrito.checkOut && ` · saída ${horaLocal(inscrito.checkOut)}`}
                  </p>
                )}
              </div>
              <div className="flex items-center gap-2">
                {estado === "sem_registro" && (
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={!liberada}
                    onClick={() => executar(() => api.checkIn(inscrito.id), "Check-in registrado.")}
                  >
                    <LogIn /> Check-in
                  </Button>
                )}
                {estado === "em_andamento" && (
                  <Button
                    size="sm"
                    onClick={() => executar(() => api.checkOut(inscrito.id), "Check-out registrado.")}
                  >
                    <LogOut /> Check-out
                  </Button>
                )}
                {estado === "presente" && (
                  <Badge className="gap-1">
                    <Check className="h-3 w-3" /> Presente
                    {inscrito.horas != null && ` · ${inscrito.horas.toLocaleString("pt-BR")} h`}
                  </Badge>
                )}
              </div>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
