import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { SeletorChips } from "@/components/SeletorChips"
import { useApp } from "@/contexto/AppContexto"
import { CAUSAS } from "@/data/ongs"
import { HABILIDADES } from "@/data/habilidades"
import { atualizarAcao, criarAcao } from "@/lib/servico"
import { hojeIso } from "@/lib/utils"

function valoresIniciais(acao, ong) {
  if (!acao) {
    return {
      titulo: "",
      descricao: "",
      causa: ong?.causa ?? "",
      unidadeId: "",
      data: "",
      horaInicio: "08:00",
      horaFim: "12:00",
      vagas: "10",
      habilidades: [],
    }
  }
  const [horaInicio, horaFim] = acao.horario.split(" às ")
  return {
    titulo: acao.titulo,
    descricao: acao.descricao,
    causa: acao.causa,
    unidadeId: String(acao.unidadeId),
    data: acao.data,
    horaInicio,
    horaFim,
    vagas: String(acao.vagas),
    habilidades: acao.habilidades,
  }
}

export function FormularioAcao({ aberto, aoFechar, acao, ong, unidades }) {
  const { executar } = useApp()
  const [valores, setValores] = useState(() => valoresIniciais(acao, ong))

  function alterar(campo, valor) {
    setValores((atual) => ({ ...atual, [campo]: valor }))
  }

  function enviar(evento) {
    evento.preventDefault()
    const resposta = executar(
      () =>
        acao
          ? atualizarAcao(acao.id, ong.id, valores)
          : criarAcao(ong.id, valores),
      acao ? "Ação atualizada com sucesso." : "Ação criada com sucesso."
    )
    if (resposta.ok) aoFechar()
  }

  return (
    <Dialog open={aberto} onOpenChange={(valor) => !valor && aoFechar()}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>{acao ? "Editar ação" : "Nova ação social"}</DialogTitle>
          <DialogDescription>
            {acao
              ? "Alterações em data, horário ou local notificam os inscritos."
              : "Voluntários compatíveis com a ação serão notificados."}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={enviar} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="acao-titulo">Título</Label>
            <Input
              id="acao-titulo"
              value={valores.titulo}
              onChange={(e) => alterar("titulo", e.target.value)}
              placeholder="Ex.: Mutirão de limpeza da praia"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="acao-descricao">Descrição</Label>
            <Textarea
              id="acao-descricao"
              rows={4}
              value={valores.descricao}
              onChange={(e) => alterar("descricao", e.target.value)}
              placeholder="Conte o que os voluntários vão fazer e o que precisam levar"
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Causa</Label>
              <Select value={valores.causa} onValueChange={(v) => alterar("causa", v)}>
                <SelectTrigger>
                  <SelectValue placeholder="Selecione" />
                </SelectTrigger>
                <SelectContent>
                  {CAUSAS.map((causa) => (
                    <SelectItem key={causa} value={causa}>
                      {causa}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Unidade</Label>
              <Select value={valores.unidadeId} onValueChange={(v) => alterar("unidadeId", v)}>
                <SelectTrigger>
                  <SelectValue placeholder="Selecione" />
                </SelectTrigger>
                <SelectContent>
                  {unidades.map((unidade) => (
                    <SelectItem key={unidade.id} value={String(unidade.id)}>
                      {unidade.nome} — {unidade.cidade}/{unidade.uf}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-4">
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="acao-data">Data</Label>
              <Input
                id="acao-data"
                type="date"
                min={hojeIso()}
                value={valores.data}
                onChange={(e) => alterar("data", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="acao-inicio">Início</Label>
              <Input
                id="acao-inicio"
                type="time"
                value={valores.horaInicio}
                onChange={(e) => alterar("horaInicio", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="acao-fim">Término</Label>
              <Input
                id="acao-fim"
                type="time"
                value={valores.horaFim}
                onChange={(e) => alterar("horaFim", e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="acao-vagas">Vagas</Label>
            <Input
              id="acao-vagas"
              type="number"
              min={1}
              value={valores.vagas}
              onChange={(e) => alterar("vagas", e.target.value)}
              className="sm:w-32"
            />
          </div>

          <div className="space-y-2">
            <Label>Habilidades desejadas (opcional)</Label>
            <SeletorChips
              rotulo="Habilidades desejadas"
              opcoes={HABILIDADES}
              valor={valores.habilidades}
              aoAlterar={(v) => alterar("habilidades", v)}
            />
          </div>

          <DialogFooter className="gap-2 sm:gap-0">
            <Button type="button" variant="outline" onClick={aoFechar}>
              Cancelar
            </Button>
            <Button type="submit">{acao ? "Salvar alterações" : "Criar ação"}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
