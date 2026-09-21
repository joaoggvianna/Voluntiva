import {
  ler,
  gravar,
  proximoId,
  lerSessao,
  gravarSessao,
} from "@/lib/armazenamento"
import { calcularCompatibilidade } from "@/lib/compatibilidade"
import {
  emailValido,
  formatarData,
  hojeIso,
  normalizarTexto,
} from "@/lib/utils"

function falhar(mensagem) {
  throw new Error(mensagem)
}

function agora() {
  return new Date().toISOString()
}

function semSenha(usuario) {
  if (!usuario) return null
  const copia = { ...usuario }
  delete copia.senha
  return copia
}

function situacaoDaAcao(acao) {
  if (acao.status === "ativa" && acao.data < hojeIso()) return "concluida"
  return acao.status
}

function detalharAcao(acao, contexto) {
  const inscritos = contexto.inscricoes.filter(
    (i) => i.acaoId === acao.id && i.status === "confirmada"
  ).length
  return {
    ...acao,
    situacao: situacaoDaAcao(acao),
    ong: contexto.ongs.find((o) => o.id === acao.ongId) ?? null,
    unidade: contexto.unidades.find((u) => u.id === acao.unidadeId) ?? null,
    inscritos,
    vagasRestantes: Math.max(acao.vagas - inscritos, 0),
  }
}

function carregarContexto() {
  return {
    ongs: ler("ongs"),
    unidades: ler("unidades"),
    inscricoes: ler("inscricoes"),
  }
}

function notificar(usuarioId, dados) {
  const notificacoes = ler("notificacoes")
  notificacoes.push({
    id: proximoId(notificacoes),
    usuarioId,
    lida: false,
    createdAt: agora(),
    ...dados,
  })
  gravar("notificacoes", notificacoes)
}

function usuariosDaOng(ongId) {
  return ler("usuarios").filter((u) => u.tipo === "ong" && u.ongId === ongId)
}

export function usuarioAtual() {
  const id = lerSessao()
  if (id === null) return null
  return semSenha(ler("usuarios").find((u) => u.id === id))
}

export function entrar(email, senha) {
  const usuario = ler("usuarios").find(
    (u) => u.email.toLowerCase() === email.trim().toLowerCase()
  )
  if (!usuario || usuario.senha !== senha) falhar("E-mail ou senha incorretos.")
  gravarSessao(usuario.id)
  return semSenha(usuario)
}

export function sair() {
  gravarSessao(null)
}

function validarCadastroBasico({ nome, email, senha }, usuarios) {
  if (!nome || nome.trim().length < 3) falhar("Informe o nome completo.")
  if (!emailValido(email ?? "")) falhar("Informe um e-mail válido.")
  if (!senha || senha.length < 6) falhar("A senha deve ter pelo menos 6 caracteres.")
  if (usuarios.some((u) => u.email.toLowerCase() === email.trim().toLowerCase())) {
    falhar("Já existe uma conta com esse e-mail.")
  }
}

export function cadastrarVoluntario(dados) {
  const usuarios = ler("usuarios")
  validarCadastroBasico(dados, usuarios)
  const usuario = {
    id: proximoId(usuarios),
    tipo: "voluntario",
    nome: dados.nome.trim(),
    email: dados.email.trim(),
    senha: dados.senha,
    telefone: dados.telefone ?? "",
    habilidades: [],
    disponibilidade: { dias: [], turnos: [] },
    createdAt: agora(),
  }
  usuarios.push(usuario)
  gravar("usuarios", usuarios)
  gravarSessao(usuario.id)
  return semSenha(usuario)
}

export function cadastrarOng(dados) {
  const usuarios = ler("usuarios")
  validarCadastroBasico(dados, usuarios)
  if (!dados.causa) falhar("Selecione a causa principal da ONG.")
  if (!dados.descricao || dados.descricao.trim().length < 20) {
    falhar("Descreva a ONG em pelo menos 20 caracteres.")
  }
  if (!dados.cidade || !dados.uf) falhar("Informe a cidade e o estado da sede.")
  const ongs = ler("ongs")
  const unidades = ler("unidades")
  const ong = {
    id: proximoId(ongs),
    nome: dados.nome.trim(),
    causa: dados.causa,
    descricao: dados.descricao.trim(),
    fundacao: new Date().getFullYear(),
    email: dados.email.trim(),
    telefone: dados.telefone ?? "",
  }
  ongs.push(ong)
  unidades.push({
    id: proximoId(unidades),
    ongId: ong.id,
    nome: "Sede",
    endereco: dados.endereco?.trim() ?? "",
    cidade: dados.cidade.trim(),
    uf: dados.uf,
    cep: dados.cep ?? "",
  })
  const usuario = {
    id: proximoId(usuarios),
    tipo: "ong",
    nome: ong.nome,
    email: dados.email.trim(),
    senha: dados.senha,
    telefone: dados.telefone ?? "",
    ongId: ong.id,
    createdAt: agora(),
  }
  usuarios.push(usuario)
  gravar("ongs", ongs)
  gravar("unidades", unidades)
  gravar("usuarios", usuarios)
  gravarSessao(usuario.id)
  return semSenha(usuario)
}

export function atualizarPerfil(usuarioId, dados) {
  const usuarios = ler("usuarios")
  const indice = usuarios.findIndex((u) => u.id === usuarioId)
  if (indice === -1) falhar("Usuário não encontrado.")
  if (!dados.nome || dados.nome.trim().length < 3) falhar("Informe o nome completo.")
  usuarios[indice] = {
    ...usuarios[indice],
    nome: dados.nome.trim(),
    telefone: dados.telefone ?? "",
    habilidades: dados.habilidades ?? usuarios[indice].habilidades,
    disponibilidade: dados.disponibilidade ?? usuarios[indice].disponibilidade,
  }
  gravar("usuarios", usuarios)
  return semSenha(usuarios[indice])
}

export function estatisticas() {
  const contexto = carregarContexto()
  const acoes = ler("acoes").map((a) => detalharAcao(a, contexto))
  return {
    ongs: contexto.ongs.length,
    acoesAbertas: acoes.filter((a) => a.situacao === "ativa").length,
    voluntarios: ler("usuarios").filter((u) => u.tipo === "voluntario").length,
    participacoes: contexto.inscricoes.filter((i) => i.status === "confirmada").length,
  }
}

export function listarAcoes(filtros = {}) {
  const contexto = carregarContexto()
  const busca = filtros.busca ? normalizarTexto(filtros.busca.trim()) : ""
  let acoes = ler("acoes").map((a) => detalharAcao(a, contexto))
  if (filtros.ongId) acoes = acoes.filter((a) => a.ongId === filtros.ongId)
  if (!filtros.incluirEncerradas) acoes = acoes.filter((a) => a.situacao === "ativa")
  if (filtros.causa) acoes = acoes.filter((a) => a.causa === filtros.causa)
  if (filtros.uf) acoes = acoes.filter((a) => a.unidade?.uf === filtros.uf)
  if (filtros.de) acoes = acoes.filter((a) => a.data >= filtros.de)
  if (filtros.ate) acoes = acoes.filter((a) => a.data <= filtros.ate)
  if (filtros.somenteComVagas) acoes = acoes.filter((a) => a.vagasRestantes > 0)
  if (busca) {
    acoes = acoes.filter((a) =>
      normalizarTexto(
        [a.titulo, a.descricao, a.ong?.nome, a.unidade?.cidade, a.causa].join(" ")
      ).includes(busca)
    )
  }
  if (filtros.compativeisCom) {
    acoes = acoes.filter(
      (a) => calcularCompatibilidade(a, filtros.compativeisCom)?.compativel
    )
  }
  return acoes.sort((a, b) => {
    if (a.situacao !== b.situacao) return a.situacao === "ativa" ? -1 : 1
    return a.situacao === "ativa"
      ? a.data.localeCompare(b.data)
      : b.data.localeCompare(a.data)
  })
}

export function obterAcao(id) {
  const acao = ler("acoes").find((a) => a.id === Number(id))
  if (!acao) return null
  return detalharAcao(acao, carregarContexto())
}

export function listarOngs(filtros = {}) {
  const contexto = carregarContexto()
  const busca = filtros.busca ? normalizarTexto(filtros.busca.trim()) : ""
  const acoes = ler("acoes").map((a) => detalharAcao(a, contexto))
  let ongs = contexto.ongs.map((ong) => ({
    ...ong,
    unidades: contexto.unidades.filter((u) => u.ongId === ong.id),
    acoesAbertas: acoes.filter((a) => a.ongId === ong.id && a.situacao === "ativa").length,
  }))
  if (filtros.causa) ongs = ongs.filter((o) => o.causa === filtros.causa)
  if (filtros.uf) ongs = ongs.filter((o) => o.unidades.some((u) => u.uf === filtros.uf))
  if (busca) {
    ongs = ongs.filter((o) =>
      normalizarTexto(
        [o.nome, o.descricao, ...o.unidades.map((u) => u.cidade)].join(" ")
      ).includes(busca)
    )
  }
  return ongs
}

export function obterOng(id) {
  return listarOngs().find((o) => o.id === Number(id)) ?? null
}

export function listarUnidades(ongId) {
  return ler("unidades").filter((u) => u.ongId === ongId)
}

function validarAcao(dados, ongId, unidades) {
  if (!dados.titulo || dados.titulo.trim().length < 5) falhar("Informe um título com pelo menos 5 caracteres.")
  if (!dados.descricao || dados.descricao.trim().length < 20) falhar("Descreva a ação em pelo menos 20 caracteres.")
  if (!dados.causa) falhar("Selecione a causa da ação.")
  if (!unidades.some((u) => u.id === Number(dados.unidadeId) && u.ongId === ongId)) {
    falhar("Selecione uma das unidades da sua ONG.")
  }
  if (!dados.data) falhar("Informe a data da ação.")
  if (!dados.horaInicio || !dados.horaFim) falhar("Informe o horário de início e de término.")
  if (dados.horaFim <= dados.horaInicio) falhar("O horário de término deve ser depois do início.")
  const vagas = Number(dados.vagas)
  if (!Number.isInteger(vagas) || vagas < 1) falhar("Informe uma quantidade de vagas válida.")
}

function montarAcao(dados) {
  return {
    unidadeId: Number(dados.unidadeId),
    titulo: dados.titulo.trim(),
    descricao: dados.descricao.trim(),
    causa: dados.causa,
    data: dados.data,
    horario: `${dados.horaInicio} às ${dados.horaFim}`,
    vagas: Number(dados.vagas),
    habilidades: dados.habilidades ?? [],
  }
}

export function criarAcao(ongId, dados) {
  validarAcao(dados, ongId, ler("unidades"))
  if (dados.data < hojeIso()) falhar("A data da ação não pode estar no passado.")
  const acoes = ler("acoes")
  const acao = {
    id: proximoId(acoes),
    ongId,
    ...montarAcao(dados),
    status: "ativa",
    createdAt: agora(),
  }
  acoes.push(acao)
  gravar("acoes", acoes)
  const ong = ler("ongs").find((o) => o.id === ongId)
  const detalhada = detalharAcao(acao, carregarContexto())
  ler("usuarios")
    .filter((u) => u.tipo === "voluntario")
    .filter((u) => calcularCompatibilidade(detalhada, u)?.compativel)
    .forEach((u) =>
      notificar(u.id, {
        tipo: "criada",
        acaoId: acao.id,
        titulo: "Nova ação com a sua cara",
        mensagem: `${ong.nome} criou a ação "${acao.titulo}" para ${formatarData(acao.data)}.`,
      })
    )
  return acao
}

export function atualizarAcao(id, ongId, dados) {
  const acoes = ler("acoes")
  const indice = acoes.findIndex((a) => a.id === id && a.ongId === ongId)
  if (indice === -1) falhar("Ação não encontrada.")
  const anterior = acoes[indice]
  if (situacaoDaAcao(anterior) !== "ativa") falhar("Só é possível editar ações ativas.")
  const unidades = ler("unidades")
  validarAcao(dados, ongId, unidades)
  if (dados.data < hojeIso()) falhar("A data da ação não pode estar no passado.")
  const atualizada = { ...anterior, ...montarAcao(dados) }
  const inscritos = ler("inscricoes").filter(
    (i) => i.acaoId === id && i.status === "confirmada"
  )
  if (atualizada.vagas < inscritos.length) {
    falhar(`Já existem ${inscritos.length} inscritos; as vagas não podem ser menores que isso.`)
  }
  acoes[indice] = atualizada
  gravar("acoes", acoes)
  const mudancas = []
  if (anterior.titulo !== atualizada.titulo) mudancas.push("título")
  if (anterior.data !== atualizada.data) mudancas.push(`data (agora ${formatarData(atualizada.data)})`)
  if (anterior.horario !== atualizada.horario) mudancas.push(`horário (agora ${atualizada.horario})`)
  if (anterior.unidadeId !== atualizada.unidadeId) {
    const unidade = unidades.find((u) => u.id === atualizada.unidadeId)
    mudancas.push(`local (agora ${unidade.nome}, ${unidade.cidade})`)
  }
  if (mudancas.length > 0) {
    inscritos.forEach((i) =>
      notificar(i.voluntarioId, {
        tipo: "atualizada",
        acaoId: id,
        titulo: "Ação atualizada",
        mensagem: `A ação "${atualizada.titulo}" teve alteração em: ${mudancas.join(", ")}.`,
      })
    )
  }
  return atualizada
}

export function cancelarAcao(id, ongId) {
  const acoes = ler("acoes")
  const indice = acoes.findIndex((a) => a.id === id && a.ongId === ongId)
  if (indice === -1) falhar("Ação não encontrada.")
  if (situacaoDaAcao(acoes[indice]) !== "ativa") falhar("Só é possível cancelar ações ativas.")
  acoes[indice] = { ...acoes[indice], status: "cancelada" }
  gravar("acoes", acoes)
  ler("inscricoes")
    .filter((i) => i.acaoId === id && i.status === "confirmada")
    .forEach((i) =>
      notificar(i.voluntarioId, {
        tipo: "cancelada",
        acaoId: id,
        titulo: "Ação cancelada",
        mensagem: `A ação "${acoes[indice].titulo}" foi cancelada pela ONG.`,
      })
    )
  return acoes[indice]
}

function validarUnidade(dados) {
  if (!dados.nome || dados.nome.trim().length < 3) falhar("Informe o nome da unidade.")
  if (!dados.endereco || dados.endereco.trim().length < 5) falhar("Informe o endereço.")
  if (!dados.cidade || dados.cidade.trim().length < 2) falhar("Informe a cidade.")
  if (!dados.uf) falhar("Selecione o estado.")
}

function montarUnidade(dados) {
  return {
    nome: dados.nome.trim(),
    endereco: dados.endereco.trim(),
    cidade: dados.cidade.trim(),
    uf: dados.uf,
    cep: dados.cep?.trim() ?? "",
  }
}

export function criarUnidade(ongId, dados) {
  validarUnidade(dados)
  const unidades = ler("unidades")
  const unidade = { id: proximoId(unidades), ongId, ...montarUnidade(dados) }
  unidades.push(unidade)
  gravar("unidades", unidades)
  return unidade
}

export function atualizarUnidade(id, ongId, dados) {
  validarUnidade(dados)
  const unidades = ler("unidades")
  const indice = unidades.findIndex((u) => u.id === id && u.ongId === ongId)
  if (indice === -1) falhar("Unidade não encontrada.")
  unidades[indice] = { ...unidades[indice], ...montarUnidade(dados) }
  gravar("unidades", unidades)
  return unidades[indice]
}

export function removerUnidade(id, ongId) {
  const unidades = ler("unidades")
  const unidade = unidades.find((u) => u.id === id && u.ongId === ongId)
  if (!unidade) falhar("Unidade não encontrada.")
  if (ler("acoes").some((a) => a.unidadeId === id)) {
    falhar("Esta unidade possui ações vinculadas e não pode ser removida.")
  }
  gravar("unidades", unidades.filter((u) => u.id !== id))
}

export function listarInscritos(acaoId) {
  const usuarios = ler("usuarios")
  return ler("inscricoes")
    .filter((i) => i.acaoId === acaoId && i.status === "confirmada")
    .map((i) => ({
      ...i,
      voluntario: semSenha(usuarios.find((u) => u.id === i.voluntarioId)),
    }))
    .filter((i) => i.voluntario)
    .sort((a, b) => a.voluntario.nome.localeCompare(b.voluntario.nome))
}

export function registrarPresenca(inscricaoId, ongId, presenca) {
  const inscricoes = ler("inscricoes")
  const indice = inscricoes.findIndex((i) => i.id === inscricaoId)
  if (indice === -1) falhar("Inscrição não encontrada.")
  const acao = ler("acoes").find((a) => a.id === inscricoes[indice].acaoId)
  if (!acao || acao.ongId !== ongId) falhar("Você não pode alterar esta inscrição.")
  if (acao.status === "cancelada") falhar("A ação foi cancelada.")
  if (acao.data > hojeIso()) falhar("A presença só pode ser registrada a partir da data da ação.")
  inscricoes[indice] = { ...inscricoes[indice], presenca }
  gravar("inscricoes", inscricoes)
  return inscricoes[indice]
}

export function obterInscricao(voluntarioId, acaoId) {
  return (
    ler("inscricoes").find(
      (i) =>
        i.voluntarioId === voluntarioId &&
        i.acaoId === acaoId &&
        i.status === "confirmada"
    ) ?? null
  )
}

export function inscrever(voluntarioId, acaoId) {
  const voluntario = ler("usuarios").find((u) => u.id === voluntarioId)
  if (!voluntario || voluntario.tipo !== "voluntario") {
    falhar("Apenas voluntários podem se inscrever em ações.")
  }
  const acao = obterAcao(acaoId)
  if (!acao) falhar("Ação não encontrada.")
  if (acao.situacao === "cancelada") falhar("Esta ação foi cancelada.")
  if (acao.situacao === "concluida") falhar("Esta ação já foi realizada.")
  if (obterInscricao(voluntarioId, acaoId)) falhar("Você já está inscrito nesta ação.")
  if (acao.vagasRestantes <= 0) falhar("Não há mais vagas disponíveis.")
  const inscricoes = ler("inscricoes")
  const existente = inscricoes.findIndex(
    (i) => i.voluntarioId === voluntarioId && i.acaoId === acaoId
  )
  let inscricao
  if (existente !== -1) {
    inscricao = { ...inscricoes[existente], status: "confirmada", presenca: null, createdAt: agora() }
    inscricoes[existente] = inscricao
  } else {
    inscricao = {
      id: proximoId(inscricoes),
      acaoId,
      voluntarioId,
      status: "confirmada",
      presenca: null,
      createdAt: agora(),
    }
    inscricoes.push(inscricao)
  }
  gravar("inscricoes", inscricoes)
  usuariosDaOng(acao.ongId).forEach((u) =>
    notificar(u.id, {
      tipo: "inscricao",
      acaoId,
      titulo: "Nova inscrição",
      mensagem: `${voluntario.nome} se inscreveu em "${acao.titulo}".`,
    })
  )
  return inscricao
}

export function cancelarInscricao(voluntarioId, acaoId) {
  const inscricoes = ler("inscricoes")
  const indice = inscricoes.findIndex(
    (i) =>
      i.voluntarioId === voluntarioId &&
      i.acaoId === acaoId &&
      i.status === "confirmada"
  )
  if (indice === -1) falhar("Inscrição não encontrada.")
  const acao = obterAcao(acaoId)
  if (acao.situacao !== "ativa") falhar("Não é possível cancelar a participação em uma ação encerrada.")
  inscricoes[indice] = { ...inscricoes[indice], status: "cancelada", presenca: null }
  gravar("inscricoes", inscricoes)
  const voluntario = ler("usuarios").find((u) => u.id === voluntarioId)
  usuariosDaOng(acao.ongId).forEach((u) =>
    notificar(u.id, {
      tipo: "inscricao",
      acaoId,
      titulo: "Inscrição cancelada",
      mensagem: `${voluntario.nome} cancelou a participação em "${acao.titulo}".`,
    })
  )
}

export function listarInscricoes(voluntarioId) {
  const contexto = carregarContexto()
  const acoes = ler("acoes")
  return contexto.inscricoes
    .filter((i) => i.voluntarioId === voluntarioId && i.status === "confirmada")
    .map((i) => ({
      ...i,
      acao: detalharAcao(acoes.find((a) => a.id === i.acaoId), contexto),
    }))
    .sort((a, b) => a.acao.data.localeCompare(b.acao.data))
}

export function historico(voluntarioId) {
  const encerradas = listarInscricoes(voluntarioId)
    .filter((i) => i.acao.situacao === "concluida")
    .sort((a, b) => b.acao.data.localeCompare(a.acao.data))
  return {
    itens: encerradas,
    total: encerradas.length,
    presentes: encerradas.filter((i) => i.presenca === "presente").length,
    ausentes: encerradas.filter((i) => i.presenca === "ausente").length,
    pendentes: encerradas.filter((i) => i.presenca === null).length,
  }
}

export function listarNotificacoes(usuarioId) {
  return ler("notificacoes")
    .filter((n) => n.usuarioId === usuarioId)
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt))
}

export function marcarNotificacaoLida(id) {
  const notificacoes = ler("notificacoes").map((n) =>
    n.id === id ? { ...n, lida: true } : n
  )
  gravar("notificacoes", notificacoes)
}

export function marcarTodasNotificacoesLidas(usuarioId) {
  const notificacoes = ler("notificacoes").map((n) =>
    n.usuarioId === usuarioId ? { ...n, lida: true } : n
  )
  gravar("notificacoes", notificacoes)
}
