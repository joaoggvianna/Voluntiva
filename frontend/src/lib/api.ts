import type { AcaoComVagas, Inscricao, TokenResponse, Usuario } from '@/types'

const BASE = import.meta.env.VITE_API_URL ?? ''
const PREFIXO = '/api/v1'

const CHAVE_TOKEN = 'voluntiva.access_token'

/* O token fica em localStorage por simplicidade do projeto acadêmico.
 * Em produção isso é vulnerável a XSS: qualquer script injetado lê o
 * token. A alternativa correta é cookie httpOnly + SameSite=Strict,
 * que exige o backend setar o cookie no login.
 * TODO(equipe): discutir com o orientador antes da entrega final. */
export const tokenStore = {
  get: () => localStorage.getItem(CHAVE_TOKEN),
  set: (t: string) => localStorage.setItem(CHAVE_TOKEN, t),
  clear: () => localStorage.removeItem(CHAVE_TOKEN),
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

async function requisicao<T>(caminho: string, init: RequestInit = {}): Promise<T> {
  const token = tokenStore.get()
  const resposta = await fetch(`${BASE}${PREFIXO}${caminho}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  })

  if (resposta.status === 401) {
    tokenStore.clear()
    throw new ApiError(401, 'Sessão expirada')
  }

  if (!resposta.ok) {
    const corpo = await resposta.json().catch(() => ({}))
    throw new ApiError(resposta.status, corpo.detail ?? corpo.mensagem ?? 'Erro na requisição')
  }

  if (resposta.status === 204) return undefined as T
  return resposta.json() as Promise<T>
}

export const api = {
  login: (email: string, senha: string) =>
    requisicao<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, senha }),
    }),

  registrar: (dados: { nome: string; email: string; senha: string }) =>
    requisicao<Usuario>('/auth/registro', {
      method: 'POST',
      body: JSON.stringify(dados),
    }),

  eu: () => requisicao<Usuario>('/auth/eu'),

  listarAcoes: (params: { status?: string; limite?: number } = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v != null).map(([k, v]) => [k, String(v)]),
    )
    return requisicao<AcaoComVagas[]>(`/acoes?${qs}`)
  },

  inscrever: (acaoId: string) =>
    requisicao<Inscricao>('/inscricoes', {
      method: 'POST',
      body: JSON.stringify({ acao_id: acaoId }),
    }),

  cancelarInscricao: (acaoId: string, motivo?: string) =>
    requisicao<Inscricao>(`/inscricoes/${acaoId}`, {
      method: 'DELETE',
      body: JSON.stringify({ motivo }),
    }),
}
