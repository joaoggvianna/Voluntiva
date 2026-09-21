import { Search, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { CAUSAS, UFS } from "@/data/ongs"

const TODAS = "todas"

export function FiltrosAcoes({ filtros, aoAlterar, aoLimpar, mostrarCompativeis }) {
  const temFiltro = Object.values(filtros).some((valor) => valor)

  return (
    <div className="space-y-4 rounded-lg border bg-card p-4">
      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={filtros.busca}
          onChange={(e) => aoAlterar({ busca: e.target.value })}
          placeholder="Buscar por título, ONG ou cidade"
          className="pl-9"
          aria-label="Buscar ações"
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="space-y-2">
          <Label>Causa</Label>
          <Select
            value={filtros.causa || TODAS}
            onValueChange={(valor) => aoAlterar({ causa: valor === TODAS ? "" : valor })}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={TODAS}>Todas as causas</SelectItem>
              {CAUSAS.map((causa) => (
                <SelectItem key={causa} value={causa}>
                  {causa}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Estado</Label>
          <Select
            value={filtros.uf || TODAS}
            onValueChange={(valor) => aoAlterar({ uf: valor === TODAS ? "" : valor })}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={TODAS}>Todos os estados</SelectItem>
              {UFS.map((uf) => (
                <SelectItem key={uf} value={uf}>
                  {uf}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="filtro-de">A partir de</Label>
          <Input
            id="filtro-de"
            type="date"
            value={filtros.de}
            onChange={(e) => aoAlterar({ de: e.target.value })}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="filtro-ate">Até</Label>
          <Input
            id="filtro-ate"
            type="date"
            value={filtros.ate}
            onChange={(e) => aoAlterar({ ate: e.target.value })}
          />
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
          <div className="flex items-center gap-2">
            <Checkbox
              id="filtro-vagas"
              checked={Boolean(filtros.vagas)}
              onCheckedChange={(marcado) => aoAlterar({ vagas: marcado ? "1" : "" })}
            />
            <Label htmlFor="filtro-vagas" className="font-normal">
              Somente com vagas
            </Label>
          </div>
          {mostrarCompativeis && (
            <div className="flex items-center gap-2">
              <Checkbox
                id="filtro-compativeis"
                checked={Boolean(filtros.compativeis)}
                onCheckedChange={(marcado) => aoAlterar({ compativeis: marcado ? "1" : "" })}
              />
              <Label htmlFor="filtro-compativeis" className="font-normal">
                Compatíveis comigo
              </Label>
            </div>
          )}
        </div>
        {temFiltro && (
          <Button variant="ghost" size="sm" onClick={aoLimpar}>
            <X /> Limpar filtros
          </Button>
        )}
      </div>
    </div>
  )
}
