/* Tradução entre o formato da API (snake_case, UUIDs, datas ISO) e o
 * formato que as telas exibem (rótulos, data local, "08:00 às 12:00").
 *
 * As telas só leem objetos produzidos aqui; nenhuma delas conhece o
 * formato cru da API. Se o contrato do backend mudar, o ajuste é neste
 * arquivo (e em src/types). */

import { DIAS, TURNOS_HORARIOS, rotuloCausa } from "@/lib/dominio"
import { formatarTelefone } from "@/lib/utils"

/* ---------------- Datas ---------------- */

function doisDigitos(n) {
  return String(n).padStart(2, "0")
}

/** "2026-12-05" no fuso do navegador. */
export function dataLocal(iso) {
  const d = new Date(iso)
  return `${d.getFullYear()}-${doisDigitos(d.getMonth() + 1)}-${doisDigitos(d.getDate())}`
}

/** "14:30" no fuso do navegador. */
export function horaLocal(iso) {
  const d = new Date(iso)
  return `${doisDigitos(d.getHours())}:${doisDigitos(d.getMinutes())}`
}

/** Data ("2026-12-05") + hora ("14:30") locais -> ISO com fuso, para a API. */
export function paraInstante(data, hora) {
  return new Date(`${data}T${hora}:00`).toISOString()
}

/* ---------------- Texto ---------------- */

export function somenteDigitos(valor) {
  return (valor ?? "").replace(/\D/g, "")
}

/** Campo opcional: string vazia vira null para a API. */
export function ouNulo(valor) {
  const texto = (valor ?? "").trim()
  return texto ? texto : null
}

function formatarCep(cep) {
  if (!cep) return ""
  return cep.length === 8 ? `${cep.slice(0, 5)}-${cep.slice(5)}` : cep
}

/* ---------------- Ações ---------------- */

/** Situação para exibição. Ação publicada cujo fim já passou é tratada
 *  como encerrada, mesmo que a ONG ainda não a tenha concluído. */
export function situacaoDaAcao(status, fim) {
  if (status === "rascunho" || status === "cancelada" || status === "concluida") return status
  return new Date(fim) < new Date() ? "concluida" : "ativa"
}

export function paraAcao(api) {
  const horaInicio = horaLocal(api.inicio)
  const horaFim = horaLocal(api.fim)
  const unidade = api.unidade_id
    ? {
        id: api.unidade_id,
        nome: api.unidade_nome,
        cidade: api.unidade_cidade,
        uf: api.unidade_uf,
        endereco: api.local_texto ?? "",
      }
    : null
  return {
    id: api.acao_id,
    codigo: api.codigo,
    ongId: api.ong_id,
    unidadeId: api.unidade_id,
    titulo: api.titulo,
    descricao: api.descricao ?? "",
    localTexto: api.local_texto ?? "",
    causa: rotuloCausa(api.causa),
    causaValor: api.causa,
    inicio: api.inicio,
    fim: api.fim,
    data: dataLocal(api.inicio),
    horaInicio,
    horaFim,
    horario: `${horaInicio} às ${horaFim}`,
    vagas: api.vagas,
    inscritos: api.vagas_ocupadas,
    vagasRestantes: Math.max(api.vagas_disponiveis, 0),
    status: api.status,
    situacao: situacaoDaAcao(api.status, api.fim),
    ong: { id: api.ong_id, nome: api.ong_nome },
    unidade,
    habilidades: api.habilidades.map((h) => h.nome),
    habilidadesDetalhe: api.habilidades,
  }
}

/** Resumo da ação que vem dentro de GET /inscricoes/minhas. */
function paraAcaoResumo(api) {
  const horaInicio = horaLocal(api.inicio)
  const horaFim = horaLocal(api.fim)
  return {
    id: api.id,
    titulo: api.titulo,
    causa: rotuloCausa(api.causa),
    data: dataLocal(api.inicio),
    horario: `${horaInicio} às ${horaFim}`,
    situacao: situacaoDaAcao(api.status, api.fim),
    ong: { id: api.ong_id, nome: api.ong_nome },
    unidade: api.unidade_cidade ? { cidade: api.unidade_cidade, uf: api.unidade_uf } : null,
    localTexto: api.local_texto ?? "",
  }
}

/** "Belo Horizonte/MG", ou o texto de local quando não há unidade. */
export function localResumo(acao) {
  if (acao.unidade?.cidade) return `${acao.unidade.cidade}/${acao.unidade.uf}`
  return acao.localTexto || "Local a definir"
}

/* ---------------- Inscrições e presença ---------------- */

export function paraMinhaInscricao(api) {
  return {
    id: api.id,
    acaoId: api.acao_id,
    status: api.status,
    checkIn: api.check_in,
    checkOut: api.check_out,
    horas: api.horas_computadas != null ? Number(api.horas_computadas) : null,
    acao: paraAcaoResumo(api.acao),
  }
}

/** Estado de presença de um inscrito, visto pela ONG. */
export function estadoPresenca(inscrito) {
  if (inscrito.checkOut) return "presente"
  if (inscrito.checkIn) return "em_andamento"
  return "sem_registro"
}

export function paraInscrito(api) {
  return {
    id: api.inscricao_id,
    status: api.status,
    checkIn: api.check_in,
    checkOut: api.check_out,
    horas: api.horas_computadas != null ? Number(api.horas_computadas) : null,
    voluntario: {
      id: api.voluntario_id,
      nome: api.nome,
      email: api.email,
      telefone: api.telefone ? formatarTelefone(api.telefone) : "",
    },
  }
}

export function paraHistorico(api) {
  const itens = api.itens.map((item) => ({
    id: item.acao_id,
    acao: {
      id: item.acao_id,
      titulo: item.acao_titulo,
      ong: { nome: item.ong_nome },
      data: dataLocal(item.inicio),
    },
    presenca: item.check_in ? "presente" : "ausente",
    horas: item.horas_computadas != null ? Number(item.horas_computadas) : null,
  }))
  return {
    itens,
    total: api.total_acoes,
    presentes: api.presencas,
    ausentes: api.ausencias,
    totalHoras: Number(api.total_horas),
  }
}

/* ---------------- ONGs e unidades ---------------- */

export function paraUnidade(api) {
  const endereco = [
    [api.logradouro, api.numero].filter(Boolean).join(", "),
    api.complemento,
    api.bairro,
  ]
    .filter(Boolean)
    .join(" - ")
  return {
    id: api.id,
    ongId: api.ong_id,
    nome: api.nome,
    endereco,
    logradouro: api.logradouro ?? "",
    cidade: api.cidade,
    uf: api.uf,
    cep: formatarCep(api.cep),
  }
}

/** Formulário de unidade (endereço num campo só) -> corpo da API. */
export function unidadeParaApi(valores) {
  const cep = somenteDigitos(valores.cep)
  return {
    nome: valores.nome.trim(),
    logradouro: ouNulo(valores.endereco),
    cidade: valores.cidade.trim(),
    uf: valores.uf,
    cep: cep || null,
  }
}

export function paraOng(api) {
  return {
    id: api.id,
    nome: api.nome,
    descricao: api.descricao ?? "",
    causa: rotuloCausa(api.causa),
    causaValor: api.causa,
    email: api.email_contato ?? "",
    telefone: api.telefone ? formatarTelefone(api.telefone) : "",
    site: api.site ?? "",
    unidades: (api.unidades ?? []).map(paraUnidade),
    acoesAbertas: api.acoes_abertas ?? 0,
  }
}

/* ---------------- Perfil e disponibilidade ---------------- */

function cobre(janela, turno) {
  return janela.hora_inicio.slice(0, 5) <= turno.inicio && janela.hora_fim.slice(0, 5) >= turno.fim
}

/** Janelas da API -> {dias, turnos} da tela (lista de nomes). */
export function janelasParaDisponibilidade(janelas) {
  const indices = new Set(janelas.map((j) => j.dia_semana))
  const dias = DIAS.filter((d) => indices.has(d.indice)).map((d) => d.nome)
  const turnos = TURNOS_HORARIOS.filter((t) => janelas.some((j) => cobre(j, t))).map((t) => t.nome)
  return { dias, turnos }
}

/** {dias, turnos} da tela -> janelas da API. Turnos vizinhos viram uma
 *  janela só (Manhã + Tarde = 06:00-18:00), para uma ação das 10h às 14h
 *  casar com quem marcou os dois. */
export function disponibilidadeParaJanelas({ dias, turnos }) {
  const marcados = TURNOS_HORARIOS.filter((t) => turnos.includes(t.nome))
  const blocos = []
  for (const turno of marcados) {
    const ultimo = blocos[blocos.length - 1]
    if (ultimo && ultimo.fim === turno.inicio) ultimo.fim = turno.fim
    else blocos.push({ inicio: turno.inicio, fim: turno.fim })
  }
  return DIAS.filter((d) => dias.includes(d.nome)).flatMap((dia) =>
    blocos.map((b) => ({ dia_semana: dia.indice, hora_inicio: b.inicio, hora_fim: b.fim }))
  )
}

export function paraPerfil(api) {
  return {
    telefone: api.telefone ? formatarTelefone(api.telefone) : "",
    cidade: api.cidade ?? "",
    uf: api.uf ?? "",
    habilidades: api.habilidades.map((h) => h.nome),
    disponibilidade: janelasParaDisponibilidade(api.disponibilidade),
  }
}

/* ---------------- Notificações ---------------- */

export function paraNotificacao(api) {
  return {
    id: api.id,
    acaoId: api.acao_id,
    tipo: api.tipo,
    titulo: api.titulo,
    mensagem: api.mensagem,
    lida: api.lida,
    createdAt: api.criada_em,
  }
}
