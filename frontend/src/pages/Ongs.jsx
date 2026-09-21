import { useSearchParams } from "react-router-dom"
import { Search, SearchX } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { CartaoOng } from "@/components/CartaoOng"
import { EstadoVazio } from "@/components/EstadoVazio"
import { CAUSAS, UFS } from "@/data/ongs"
import { listarOngs } from "@/lib/servico"

const TODAS = "todas"

export function Ongs() {
  const [params, setParams] = useSearchParams()
  const busca = params.get("busca") ?? ""
  const causa = params.get("causa") ?? ""
  const uf = params.get("uf") ?? ""

  function alterar(campo, valor) {
    const proximo = new URLSearchParams(params)
    if (valor) proximo.set(campo, valor)
    else proximo.delete(campo)
    setParams(proximo, { replace: true })
  }

  const ongs = listarOngs({ busca, causa, uf })

  return (
    <div className="container mx-auto space-y-6 px-4 py-10">
      <div>
        <h1 className="text-3xl font-bold">ONGs</h1>
        <p className="mt-2 text-muted-foreground">
          Conheça as organizações que promovem ações de voluntariado.
        </p>
      </div>

      <div className="grid gap-3 rounded-lg border bg-card p-4 sm:grid-cols-[1fr_200px_140px_auto]">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={busca}
            onChange={(e) => alterar("busca", e.target.value)}
            placeholder="Buscar por nome ou cidade"
            className="pl-9"
            aria-label="Buscar ONGs"
          />
        </div>
        <Select
          value={causa || TODAS}
          onValueChange={(valor) => alterar("causa", valor === TODAS ? "" : valor)}
        >
          <SelectTrigger aria-label="Causa">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={TODAS}>Todas as causas</SelectItem>
            {CAUSAS.map((item) => (
              <SelectItem key={item} value={item}>
                {item}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select
          value={uf || TODAS}
          onValueChange={(valor) => alterar("uf", valor === TODAS ? "" : valor)}
        >
          <SelectTrigger aria-label="Estado">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={TODAS}>Todos</SelectItem>
            {UFS.map((item) => (
              <SelectItem key={item} value={item}>
                {item}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {(busca || causa || uf) && (
          <Button variant="ghost" onClick={() => setParams({}, { replace: true })}>
            Limpar
          </Button>
        )}
      </div>

      {ongs.length === 0 ? (
        <EstadoVazio
          icone={SearchX}
          titulo="Nenhuma ONG encontrada"
          descricao="Tente buscar por outro termo ou remover os filtros."
        />
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {ongs.map((ong) => (
            <CartaoOng key={ong.id} ong={ong} />
          ))}
        </div>
      )}
    </div>
  )
}
