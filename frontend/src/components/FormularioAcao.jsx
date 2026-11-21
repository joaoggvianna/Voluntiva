import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
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
import { ouNulo, paraInstante } from "@/lib/adaptadores"
import { api } from "@/lib/api"
import { CAUSAS } from "@/lib/dominio"
import { hojeIso } from "@/lib/utils"

function valoresIniciais(acao, ong) {
  if (!acao) {
    return {
      titulo: "",
      descricao: "",
      causa: ong?.causaValor ?? "",
      unidadeId: "",
      localTexto: "",
      data: "",
      horaInicio: "08:00",
      horaFim: "12:00",
      vagas: "10",
      habilidades: [],
      publicar: true,
    }
  }
  return {
    titulo: acao.titulo,
    descricao: acao.descricao,
    causa: acao.causaValor ?? "",
    unidadeId: acao.unidadeId ?? "",
    localTexto: acao.localTexto,
    data: acao.data,
    horaInicio: acao.horaInicio,
    horaFim: acao.horaFim,
    vagas: String(acao.vagas),
    habilidades: acao.habilidades,
    publicar: false,
  }
}

function validar(valores, unidades, editando) {
  if (valores.titulo.trim().length < 5) return "Informe um título com pelo menos 5 caracteres."
  if (valores.descricao.trim().length < 20) return "Descreva a ação em pelo menos 20 caracteres."
  if (!valores.causa) return "Selecione a causa da ação."
  if (!unidades.some((u) => u.id === valores.unidadeId)) return "Selecione uma das unidades da sua ONG."
  if (!valores.data) return "Informe a data da ação."
  if (!valores.horaInicio || !valores.horaFim) return "Informe o horário de início e de término."
  if (valores.horaFim <= valores.horaInicio) return "O horário de término deve ser depois do início."
  const vagas = Number(valores.vagas)
  if (!Number.isInteger(vagas) || vagas < 1) return "Informe uma quantidade de vagas válida."
  if (!editando && valores.data < hojeIso()) return "A data da ação não pode estar no passado."
  return null
}

export function FormularioAcao({ aberto, aoFechar, acao, ong, unidades }) {
  const { executar, catalogoHabilidades } = useApp()
  const [valores, setValores] = useState(() => valoresIniciais(acao, ong))
  const [erro, setErro] = useState(null)
  const [enviando, setEnviando] = useState(false)

  function alterar(campo, valor) {
    setValores((atual) => ({ ...atual, [campo]: valor }))
  }

  async function enviar(evento) {
    evento.preventDefault()
    const problema = validar(valores, unidades, Boolean(acao))
    setErro(problema)
    if (problema) return

    const idPorNome = Object.fromEntries(catalogoHabilidades.map((h) => [h.nome, h.id]))
    const corpo = {
      titulo: valores.titulo.trim(),
      descricao: valores.descricao.trim(),
      causa: valores.causa,
      unidade_id: valores.unidadeId,
      local_texto: ouNulo(valores.localTexto),
      inicio: paraInstante(valores.data, valores.horaInicio),
      fim: paraInstante(valores.data, valores.horaFim),
      vagas: Number(valores.vagas),
      habilidades: valores.habilidades.map((nome) => idPorNome[nome]).filter(Boolean),
    }

    setEnviando(true)
    const resposta = await executar(
      () =>
        acao
          ? api.atualizarAcao(acao.id, corpo)
          : api.criarAcao({
              ...corpo,
              ong_id: ong.id,
              status: valores.publicar ? "publicada" : "rascunho",
            }),
      acao
        ? "Ação atualizada com sucesso."
        : valores.publicar
          ? "Ação publicada."
          : "Rascunho salvo."
    )
    setEnviando(false)
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
              : "Ao publicar, os voluntários compatíveis com a ação são notificados."}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={enviar} className="space-y-4" noValidate>
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
                    <SelectItem key={causa.valor} value={causa.valor}>
                      {causa.rotulo}
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
                    <SelectItem key={unidade.id} value={unidade.id}>
                      {unidade.nome} — {unidade.cidade}/{unidade.uf}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="acao-local">Ponto de encontro (opcional)</Label>
            <Input
              id="acao-local"
              value={valores.localTexto}
              onChange={(e) => alterar("localTexto", e.target.value)}
              placeholder="Ex.: Portão 2 do parque"
            />
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
            {acao && acao.inscritos > 0 && (
              <p className="text-xs text-muted-foreground">
                Já há {acao.inscritos} inscritos: as vagas não podem ficar abaixo disso.
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label>Habilidades desejadas (opcional)</Label>
            <SeletorChips
              rotulo="Habilidades desejadas"
              opcoes={catalogoHabilidades.map((h) => h.nome)}
              valor={valores.habilidades}
              aoAlterar={(v) => alterar("habilidades", v)}
            />
          </div>

          {!acao && (
            <div className="flex items-center gap-2">
              <Checkbox
                id="acao-publicar"
                checked={valores.publicar}
                onCheckedChange={(marcado) => alterar("publicar", Boolean(marcado))}
              />
              <Label htmlFor="acao-publicar" className="font-normal">
                Publicar agora (desmarque para salvar como rascunho)
              </Label>
            </div>
          )}

          {erro && (
            <p className="text-sm text-destructive" role="alert">
              {erro}
            </p>
          )}

          <DialogFooter className="gap-2 sm:gap-0">
            <Button type="button" variant="outline" onClick={aoFechar}>
              Cancelar
            </Button>
            <Button type="submit" disabled={enviando}>
              {enviando ? "Salvando..." : acao ? "Salvar alterações" : "Criar ação"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
