import { useState } from "react"
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom"
import { Building2, User } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import { useApp } from "@/contexto/AppContexto"
import { CAUSAS, UFS } from "@/data/ongs"
import { cadastrarOng, cadastrarVoluntario } from "@/lib/servico"
import { emailValido, formatarTelefone } from "@/lib/utils"

function Campo({ id, rotulo, erro, children }) {
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>{rotulo}</Label>
      {children}
      {erro && <p className="text-sm text-destructive">{erro}</p>}
    </div>
  )
}

function validar(tipo, valores) {
  const erros = {}
  if (valores.nome.trim().length < 3) {
    erros.nome = tipo === "ong" ? "Informe o nome da ONG." : "Informe o seu nome completo."
  }
  if (!emailValido(valores.email)) erros.email = "Informe um e-mail válido."
  if (valores.senha.length < 6) erros.senha = "A senha deve ter pelo menos 6 caracteres."
  if (valores.senha !== valores.confirmacao) erros.confirmacao = "As senhas não conferem."
  if (tipo === "ong") {
    if (!valores.causa) erros.causa = "Selecione a causa principal."
    if (valores.descricao.trim().length < 20) {
      erros.descricao = "Descreva a ONG em pelo menos 20 caracteres."
    }
    if (valores.cidade.trim().length < 2) erros.cidade = "Informe a cidade da sede."
    if (!valores.uf) erros.uf = "Selecione o estado."
  }
  return erros
}

export function Cadastro() {
  const { usuario, executar } = useApp()
  const navegar = useNavigate()
  const [params, setParams] = useSearchParams()
  const tipo = params.get("tipo") === "ong" ? "ong" : "voluntario"
  const [erros, setErros] = useState({})
  const [valores, setValores] = useState({
    nome: "",
    email: "",
    telefone: "",
    senha: "",
    confirmacao: "",
    causa: "",
    descricao: "",
    endereco: "",
    cidade: "",
    uf: "",
    cep: "",
  })

  if (usuario) return <Navigate to="/painel" replace />

  function alterar(campo, valor) {
    setValores((atual) => ({ ...atual, [campo]: valor }))
  }

  function enviar(evento) {
    evento.preventDefault()
    const novosErros = validar(tipo, valores)
    setErros(novosErros)
    if (Object.keys(novosErros).length > 0) return
    const resposta = executar(
      () => (tipo === "ong" ? cadastrarOng(valores) : cadastrarVoluntario(valores)),
      "Conta criada com sucesso!"
    )
    if (resposta.ok) navegar("/painel", { replace: true })
  }

  return (
    <div className="container mx-auto max-w-2xl px-4 py-12">
      <Card>
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Criar conta</CardTitle>
          <CardDescription>
            Escolha o tipo de conta e preencha seus dados.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <Tabs
            value={tipo}
            onValueChange={(valor) => {
              setErros({})
              setParams(valor === "ong" ? { tipo: "ong" } : {}, { replace: true })
            }}
          >
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="voluntario" className="gap-2">
                <User className="h-4 w-4" /> Sou voluntário
              </TabsTrigger>
              <TabsTrigger value="ong" className="gap-2">
                <Building2 className="h-4 w-4" /> Sou uma ONG
              </TabsTrigger>
            </TabsList>
          </Tabs>

          <form onSubmit={enviar} className="space-y-4" noValidate>
            <Campo
              id="nome"
              rotulo={tipo === "ong" ? "Nome da ONG" : "Nome completo"}
              erro={erros.nome}
            >
              <Input
                id="nome"
                value={valores.nome}
                onChange={(e) => alterar("nome", e.target.value)}
                aria-invalid={Boolean(erros.nome)}
              />
            </Campo>

            <div className="grid gap-4 sm:grid-cols-2">
              <Campo id="email" rotulo="E-mail" erro={erros.email}>
                <Input
                  id="email"
                  type="email"
                  autoComplete="email"
                  value={valores.email}
                  onChange={(e) => alterar("email", e.target.value)}
                  aria-invalid={Boolean(erros.email)}
                />
              </Campo>
              <Campo id="telefone" rotulo="Telefone (opcional)">
                <Input
                  id="telefone"
                  inputMode="tel"
                  value={valores.telefone}
                  onChange={(e) => alterar("telefone", formatarTelefone(e.target.value))}
                  placeholder="(11) 99999-9999"
                />
              </Campo>
            </div>

            {tipo === "ong" && (
              <>
                <Campo id="causa" rotulo="Causa principal" erro={erros.causa}>
                  <Select value={valores.causa} onValueChange={(v) => alterar("causa", v)}>
                    <SelectTrigger id="causa" aria-invalid={Boolean(erros.causa)}>
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
                </Campo>

                <Campo id="descricao" rotulo="Sobre a ONG" erro={erros.descricao}>
                  <Textarea
                    id="descricao"
                    rows={4}
                    value={valores.descricao}
                    onChange={(e) => alterar("descricao", e.target.value)}
                    placeholder="Conte a missão e o trabalho da organização"
                    aria-invalid={Boolean(erros.descricao)}
                  />
                </Campo>

                <div className="space-y-4 rounded-lg border p-4">
                  <p className="text-sm font-medium">Endereço da sede</p>
                  <Campo id="endereco" rotulo="Endereço (opcional)">
                    <Input
                      id="endereco"
                      value={valores.endereco}
                      onChange={(e) => alterar("endereco", e.target.value)}
                    />
                  </Campo>
                  <div className="grid gap-4 sm:grid-cols-6">
                    <div className="sm:col-span-3">
                      <Campo id="cidade" rotulo="Cidade" erro={erros.cidade}>
                        <Input
                          id="cidade"
                          value={valores.cidade}
                          onChange={(e) => alterar("cidade", e.target.value)}
                          aria-invalid={Boolean(erros.cidade)}
                        />
                      </Campo>
                    </div>
                    <div className="sm:col-span-1">
                      <Campo id="uf" rotulo="UF" erro={erros.uf}>
                        <Select value={valores.uf} onValueChange={(v) => alterar("uf", v)}>
                          <SelectTrigger id="uf" aria-invalid={Boolean(erros.uf)}>
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
                      </Campo>
                    </div>
                    <div className="sm:col-span-2">
                      <Campo id="cep" rotulo="CEP (opcional)">
                        <Input
                          id="cep"
                          value={valores.cep}
                          onChange={(e) => alterar("cep", e.target.value)}
                        />
                      </Campo>
                    </div>
                  </div>
                </div>
              </>
            )}

            <div className="grid gap-4 sm:grid-cols-2">
              <Campo id="senha" rotulo="Senha" erro={erros.senha}>
                <Input
                  id="senha"
                  type="password"
                  autoComplete="new-password"
                  value={valores.senha}
                  onChange={(e) => alterar("senha", e.target.value)}
                  aria-invalid={Boolean(erros.senha)}
                />
              </Campo>
              <Campo id="confirmacao" rotulo="Confirmar senha" erro={erros.confirmacao}>
                <Input
                  id="confirmacao"
                  type="password"
                  autoComplete="new-password"
                  value={valores.confirmacao}
                  onChange={(e) => alterar("confirmacao", e.target.value)}
                  aria-invalid={Boolean(erros.confirmacao)}
                />
              </Campo>
            </div>

            <Button type="submit" className="w-full">
              {tipo === "ong" ? "Cadastrar ONG" : "Criar minha conta"}
            </Button>
          </form>

          <p className="text-center text-sm text-muted-foreground">
            Já tem conta?{" "}
            <Link to="/entrar" className="font-medium text-primary hover:underline">
              Entrar
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
