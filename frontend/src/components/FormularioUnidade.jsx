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
import { UFS } from "@/data/ongs"
import { atualizarUnidade, criarUnidade } from "@/lib/servico"

export function FormularioUnidade({ aberto, aoFechar, unidade, ongId }) {
  const { executar } = useApp()
  const [valores, setValores] = useState(() => ({
    nome: unidade?.nome ?? "",
    endereco: unidade?.endereco ?? "",
    cidade: unidade?.cidade ?? "",
    uf: unidade?.uf ?? "",
    cep: unidade?.cep ?? "",
  }))

  function alterar(campo, valor) {
    setValores((atual) => ({ ...atual, [campo]: valor }))
  }

  function enviar(evento) {
    evento.preventDefault()
    const resposta = executar(
      () =>
        unidade
          ? atualizarUnidade(unidade.id, ongId, valores)
          : criarUnidade(ongId, valores),
      unidade ? "Unidade atualizada." : "Unidade cadastrada."
    )
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

        <form onSubmit={enviar} className="space-y-4">
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
            <Label htmlFor="unidade-endereco">Endereço</Label>
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
          <DialogFooter className="gap-2 sm:gap-0">
            <Button type="button" variant="outline" onClick={aoFechar}>
              Cancelar
            </Button>
            <Button type="submit">{unidade ? "Salvar" : "Cadastrar unidade"}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
