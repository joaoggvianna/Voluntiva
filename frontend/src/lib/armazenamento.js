import { ongs as ongsSeed } from "@/data/ongs"
import { acoesSeed } from "@/data/acoes"
import { usuariosSeed } from "@/data/usuarios"
import { inscricoesSeed } from "@/data/inscricoes"
import { notificacoesSeed } from "@/data/notificacoes"

const PREFIXO = "voluntiva:"
const VERSAO_DO_BANCO = "1"
const memoria = {}

function lerBruto(chave) {
  try {
    const valor = window.localStorage.getItem(PREFIXO + chave)
    if (valor !== null) return valor
  } catch {
    return memoria[chave] ?? null
  }
  return memoria[chave] ?? null
}

function gravarBruto(chave, valor) {
  memoria[chave] = valor
  try {
    window.localStorage.setItem(PREFIXO + chave, valor)
  } catch {
    return
  }
}

function removerBruto(chave) {
  delete memoria[chave]
  try {
    window.localStorage.removeItem(PREFIXO + chave)
  } catch {
    return
  }
}

export function ler(tabela, padrao = []) {
  const bruto = lerBruto(tabela)
  if (bruto === null) return padrao
  try {
    return JSON.parse(bruto)
  } catch {
    return padrao
  }
}

export function gravar(tabela, valor) {
  gravarBruto(tabela, JSON.stringify(valor))
}

export function remover(tabela) {
  removerBruto(tabela)
}

export function proximoId(lista) {
  return lista.reduce((maior, item) => Math.max(maior, item.id), 0) + 1
}

export function iniciarBanco() {
  if (lerBruto("versao") === VERSAO_DO_BANCO) return
  const unidades = ongsSeed.flatMap((ong) =>
    ong.unidades.map((unidade) => ({ ...unidade, ongId: ong.id }))
  )
  const ongs = ongsSeed.map((ong) => {
    const copia = { ...ong }
    delete copia.unidades
    return copia
  })
  gravar("ongs", ongs)
  gravar("unidades", unidades)
  gravar("acoes", acoesSeed)
  gravar("usuarios", usuariosSeed)
  gravar("inscricoes", inscricoesSeed)
  gravar("notificacoes", notificacoesSeed)
  removerBruto("sessao")
  gravarBruto("versao", VERSAO_DO_BANCO)
}

export function reiniciarBanco() {
  removerBruto("versao")
  iniciarBanco()
}

export function lerSessao() {
  const bruto = lerBruto("sessao")
  return bruto === null ? null : Number(bruto)
}

export function gravarSessao(usuarioId) {
  if (usuarioId === null) removerBruto("sessao")
  else gravarBruto("sessao", String(usuarioId))
}
