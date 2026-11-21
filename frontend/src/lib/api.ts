/* ---------------------------------------------------------------------
 * Cliente da API REST do backend (backend/app/api/v1).
 *
 * Única porta de saída da interface para o servidor: as telas chamam
 * estas funções (via src/lib/adaptadores.js quando precisam do formato
 * de exibição) e nunca usam fetch diretamente.
 *
 * Sessão: access token curto + refresh token. Uma resposta 401 dispara
 * UMA tentativa de renovação (compartilhada entre requisições
 * simultâneas); se falhar, a sessão é encerrada e quem escuta
 * `aoExpirarSessao` é avisado.
 * ------------------------------------------------------------------ */

import type {
  AcaoComVagas,
  AcaoDados,
  AcaoGravada,
  AcaoNova,
  Estatisticas,
  FiltrosAcoes,
  Habilidade,
  Historico,
  Inscricao,
  InscricaoComAcao,
  Inscrito,
  MinhaOng,
  Notificacao,
  OngCadastro,
  OngPublica,
  Pagina,
  PerfilAtualizacao,
  PerfilVoluntario,
  Presenca,
  TokenResponse,
  Unidade,
  UnidadeDados,
  Usuario,
} from '@/types'

const BASE = import.meta.env.VITE_API_URL ?? ''
const PREFIXO = '/api/v1'

const CHAVE_ACCESS = 'voluntiva.access_token'
const CHAVE_REFRESH = 'voluntiva.refresh_token'

/* Os tokens ficam em localStorage por simplicidade do projeto acadêmico.
 * Em produção isso é vulnerável a XSS: qualquer script injetado lê o
 * token. A alternativa correta é cookie httpOnly + SameSite=Strict,
 * que exige o backend setar o cookie no login (limitação documentada). */
function ler(chave: string): string | null {
  try {
    return localStorage.getItem(chave)
  } catch {
    return null
  }
}

export const tokenStore = {
  get: () => ler(CHAVE_ACCESS),
  getRefresh: () => ler(CHAVE_REFRESH),
  set: (access: string, refresh?: string) => {
    localStorage.setItem(CHAVE_ACCESS, access)
    if (refresh) localStorage.setItem(CHAVE_REFRESH, refresh)
  },
  clear: () => {
    localStorage.removeItem(CHAVE_ACCESS)
    localStorage.removeItem(CHAVE_REFRESH)
  },
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

type Ouvinte = () => void
const ouvintesExpiracao = new Set<Ouvinte>()

/** Registra quem deve saber que a sessão acabou. Devolve a função de remoção. */
export function aoExpirarSessao(ouvinte: Ouvinte): () => void {
  ouvintesExpiracao.add(ouvinte)
  return () => ouvintesExpiracao.delete(ouvinte)
}

function mensagemDeErro(corpo: unknown, status: number): string {
  const dados = corpo as { detail?: unknown; mensagem?: string }
  if (typeof dados?.detail === 'string') return dados.detail
  if (Array.isArray(dados?.detail)) {
    // Erro de validação do FastAPI: lista de {loc, msg}.
    const primeiro = dados.detail[0] as { msg?: string; loc?: unknown[] } | undefined
    if (primeiro?.msg) {
      const campo = primeiro.loc?.[primeiro.loc.length - 1]
      const texto = primeiro.msg.replace(/^Value error, /, '')
      return typeof campo === 'string' && campo !== 'body' ? `${campo}: ${texto}` : texto
    }
  }
  if (dados?.mensagem) return dados.mensagem
  if (status >= 500) return 'O servidor encontrou um erro. Tente novamente em instantes.'
  return 'Não foi possível concluir a operação.'
}

let renovacaoEmAndamento: Promise<boolean> | null = null

async function renovarSessao(): Promise<boolean> {
  const refresh = tokenStore.getRefresh()
  if (!refresh) return false
  renovacaoEmAndamento ??= (async () => {
    try {
      const resposta = await fetch(`${BASE}${PREFIXO}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refresh }),
      })
      if (!resposta.ok) return false
      const dados = (await resposta.json()) as TokenResponse
      tokenStore.set(dados.access_token, dados.refresh_token)
      return true
    } catch {
      return false
    } finally {
      renovacaoEmAndamento = null
    }
  })()
  return renovacaoEmAndamento
}

interface Resposta<T> {
  dados: T
  cabecalhos: Headers
}

async function enviar<T>(
  caminho: string,
  init: RequestInit = {},
  tentouRenovar = false,
): Promise<Resposta<T>> {
  const token = tokenStore.get()
  let resposta: Response
  try {
    resposta = await fetch(`${BASE}${PREFIXO}${caminho}`, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...init.headers,
      },
    })
  } catch {
    throw new ApiError(0, 'Não foi possível falar com o servidor. Verifique sua conexão.')
  }

  if (resposta.status === 401 && token) {
    if (!tentouRenovar && (await renovarSessao())) {
      return enviar<T>(caminho, init, true)
    }
    tokenStore.clear()
    ouvintesExpiracao.forEach((ouvinte) => ouvinte())
    throw new ApiError(401, 'Sua sessão expirou. Entre novamente.')
  }

  if (!resposta.ok) {
    const corpo = await resposta.json().catch(() => ({}))
    throw new ApiError(resposta.status, mensagemDeErro(corpo, resposta.status))
  }

  const dados = resposta.status === 204 ? (undefined as T) : ((await resposta.json()) as T)
  return { dados, cabecalhos: resposta.headers }
}

async function requisicao<T>(caminho: string, init: RequestInit = {}): Promise<T> {
  return (await enviar<T>(caminho, init)).dados
}

function consulta(params: object): string {
  const pares = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== null && v !== '' && v !== false)
    .map(([k, v]) => [k, String(v)])
  const qs = new URLSearchParams(pares).toString()
  return qs ? `?${qs}` : ''
}

const json = (corpo: unknown): RequestInit => ({ body: JSON.stringify(corpo) })
const id = encodeURIComponent

export const api = {
  /* ---------------- Autenticação ---------------- */
  login: async (email: string, senha: string) => {
    const dados = await requisicao<TokenResponse>('/auth/login', {
      method: 'POST', ...json({ email, senha }),
    })
    tokenStore.set(dados.access_token, dados.refresh_token)
    return dados.usuario
  },

  registrarVoluntario: (dados: { nome: string; email: string; senha: string; telefone?: string | null }) =>
    requisicao<Usuario>('/auth/registro', { method: 'POST', ...json(dados) }),

  sair: () => tokenStore.clear(),

  eu: () => requisicao<Usuario>('/auth/eu'),

  temSessao: () => Boolean(tokenStore.get()),

  /* ---------------- Ações ---------------- */
  listarAcoes: async (filtros: FiltrosAcoes = {}): Promise<Pagina<AcaoComVagas>> => {
    const { dados, cabecalhos } = await enviar<AcaoComVagas[]>(`/acoes${consulta(filtros)}`)
    return { itens: dados, total: Number(cabecalhos.get('X-Total-Count') ?? dados.length) }
  },

  acoesCompativeis: async (limite = 100): Promise<Pagina<AcaoComVagas>> => {
    const { dados, cabecalhos } = await enviar<AcaoComVagas[]>(
      `/acoes/compativeis${consulta({ limite })}`,
    )
    return { itens: dados, total: Number(cabecalhos.get('X-Total-Count') ?? dados.length) }
  },

  obterAcao: (acaoId: string) => requisicao<AcaoComVagas>(`/acoes/${id(acaoId)}`),

  criarAcao: (dados: AcaoNova) =>
    requisicao<AcaoGravada>('/acoes', { method: 'POST', ...json(dados) }),

  atualizarAcao: (acaoId: string, dados: AcaoDados) =>
    requisicao<AcaoGravada>(`/acoes/${id(acaoId)}`, { method: 'PATCH', ...json(dados) }),

  listarInscritos: (acaoId: string) =>
    requisicao<Inscrito[]>(`/acoes/${id(acaoId)}/inscricoes`),

  /* ---------------- Inscrições e presença ---------------- */
  minhasInscricoes: () => requisicao<InscricaoComAcao[]>('/inscricoes/minhas'),

  /** Com `listaEspera`, ação lotada coloca o voluntário na fila em vez de recusar. */
  inscrever: (acaoId: string, listaEspera = false) =>
    requisicao<Inscricao>('/inscricoes', {
      method: 'POST', ...json({ acao_id: acaoId, lista_espera: listaEspera }),
    }),

  cancelarInscricao: (acaoId: string, motivo?: string) =>
    requisicao<Inscricao>(`/inscricoes/${id(acaoId)}`, {
      method: 'DELETE', ...json({ motivo: motivo ?? null }),
    }),

  checkIn: (inscricaoId: string) =>
    requisicao<Presenca>(`/inscricoes/${id(inscricaoId)}/check-in`, { method: 'POST' }),

  checkOut: (inscricaoId: string) =>
    requisicao<Presenca>(`/inscricoes/${id(inscricaoId)}/check-out`, { method: 'POST' }),

  /* ---------------- ONGs e unidades ---------------- */
  cadastrarOng: (dados: OngCadastro) =>
    requisicao<Usuario>('/ongs', { method: 'POST', ...json(dados) }),

  listarOngs: (filtros: { busca?: string; uf?: string; causa?: string } = {}) =>
    requisicao<OngPublica[]>(`/ongs${consulta({ ...filtros, limite: 100 })}`),

  obterOng: (ongId: string) => requisicao<OngPublica>(`/ongs/${id(ongId)}`),

  minhasOngs: () => requisicao<MinhaOng[]>('/ongs/minhas'),

  listarUnidades: (ongId: string) => requisicao<Unidade[]>(`/ongs/${id(ongId)}/unidades`),

  criarUnidade: (ongId: string, dados: UnidadeDados) =>
    requisicao<Unidade>(`/ongs/${id(ongId)}/unidades`, { method: 'POST', ...json(dados) }),

  atualizarUnidade: (ongId: string, unidadeId: string, dados: UnidadeDados) =>
    requisicao<Unidade>(`/ongs/${id(ongId)}/unidades/${id(unidadeId)}`, {
      method: 'PATCH', ...json(dados),
    }),

  removerUnidade: (ongId: string, unidadeId: string) =>
    requisicao<void>(`/ongs/${id(ongId)}/unidades/${id(unidadeId)}`, { method: 'DELETE' }),

  /* ---------------- Voluntário ---------------- */
  habilidades: () => requisicao<Habilidade[]>('/habilidades'),

  meuPerfil: () => requisicao<PerfilVoluntario>('/voluntarios/eu'),

  atualizarPerfil: (dados: PerfilAtualizacao) =>
    requisicao<PerfilVoluntario>('/voluntarios/eu', { method: 'PUT', ...json(dados) }),

  historico: () => requisicao<Historico>('/voluntarios/eu/historico'),

  /* ---------------- Notificações ---------------- */
  notificacoes: (limite = 50) => requisicao<Notificacao[]>(`/notificacoes${consulta({ limite })}`),

  contarNaoLidas: () => requisicao<{ nao_lidas: number }>('/notificacoes/nao-lidas'),

  marcarLida: (notificacaoId: string) =>
    requisicao<Notificacao>(`/notificacoes/${id(notificacaoId)}/lida`, { method: 'POST' }),

  marcarTodasLidas: () =>
    requisicao<{ marcadas: number }>('/notificacoes/lidas', { method: 'POST' }),

  /* ---------------- Página inicial ---------------- */
  estatisticas: () => requisicao<Estatisticas>('/estatisticas'),
}
