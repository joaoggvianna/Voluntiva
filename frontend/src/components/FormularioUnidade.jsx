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
import { useApp } from "@/contexto/AppContexto"
import { somenteDigitos, unidadeParaApi } from "@/lib/adaptadores"
import { api } from "@/lib/api"
import { UFS } from "@/lib/dominio"

function validar(valores) {
  if (valores.nome.trim().length < 3) return "Informe o nome da unidade."
  if (valores.cidade.trim().length < 2) return "Informe a cidade."
  if (!valores.uf) return "Selecione o estado."
  const cep = somenteDigitos(valores.cep)
  if (cep && cep.length !== 8) return "O CEP deve ter 8 dígitos."
  return null
}

export function FormularioUnidade({ aberto, aoFechar, unidade, ongId }) {
  const { executar } = useApp()
  const [erro, setErro] = useState(null)
  const [enviando, setEnviando] = useState(false)
  const [valores, setValores] = useState(() => ({
    nome: unidade?.nome ?? "",
    endereco: unidade?.logradouro ?? "",
    cidade: unidade?.cidade ?? "",
    uf: unidade?.uf ?? "",
    cep: unidade?.cep ?? "",
  }))

  function alterar(campo, valor) {
    setValores((atual) => ({ ...atual, [campo]: valor }))
  }

  async function enviar(evento) {
    evento.preventDefault()
    const problema = validar(valores)
    setErro(problema)
    if (problema) return
    const corpo = unidadeParaApi(valores)
    setEnviando(true)
    const resposta = await executar(
      () =>
        unidade
          ? api.atualizarUnidade(ongId, unidade.id, corpo)
          : api.criarUnidade(ongId, corpo),
      unidade ? "Unidade atualizada." : "Unidade cadastrada."
    )
    setEnviando(false)
    if (resposta.ok) aoFechar()
  }

  return (
    <Dialog open={aberto} onOpenChange={(valor) => !valor && aoFechar()}>
      <DialogContent className="max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{unidade ? "Editar unidade" : "Nova unidade"}</DialogTitle>
          <DialogDescription>
            As ações são realizadas em uma das unidades da ONG.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={enviar} className="space-y-4" noValidate>
          <div className="space-y-2">
            <Label htmlFor="unidade-nome">Nome da unidade</Label>
            <Input
              id="unidade-nome"
              value={valores.nome}
              onChange={(e) => alterar("nome", e.target.value)}
              placeholder="Ex.: Núcleo Zona Sul"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="unidade-endereco">Endereço (opcional)</Label>
            <Input
              id="unidade-endereco"
              value={valores.endereco}
              onChange={(e) => alterar("endereco", e.target.value)}
              placeholder="Rua, número e bairro"
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-6">
            <div className="space-y-2 sm:col-span-3">
              <Label htmlFor="unidade-cidade">Cidade</Label>
              <Input
                id="unidade-cidade"
                value={valores.cidade}
                onChange={(e) => alterar("cidade", e.target.value)}
              />
            </div>
            <div className="space-y-2 sm:col-span-1">
              <Label>UF</Label>
              <Select value={valores.uf} onValueChange={(v) => alterar("uf", v)}>
                <SelectTrigger>
                  <SelectValue placeholder="UF" />
                </SelectTrigger>
                <SelectContent>
                  {UFS.map((uf) => (
                    <SelectItem key={uf} value={uf}>
                      {uf}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="unidade-cep">CEP</Label>
              <Input
                id="unidade-cep"
                value={valores.cep}
                onChange={(e) => alterar("cep", e.target.value)}
                placeholder="00000-000"
              />
            </div>
          </div>
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
              {enviando ? "Salvando..." : unidade ? "Salvar" : "Cadastrar unidade"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
