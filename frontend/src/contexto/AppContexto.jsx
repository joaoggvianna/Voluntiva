import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react"
import { toast } from "sonner"
import { aoExpirarSessao, api } from "@/lib/api"
import { paraNotificacao, paraPerfil } from "@/lib/adaptadores"
import { conectarNotificacoes } from "@/lib/ws"

const AppContexto = createContext(null)

/** Monta o usuário da sessão: dados da conta + perfil (voluntário) ou
 *  ONGs que gere (conta de ONG). */
async function carregarUsuario() {
  const conta = await api.eu()
  if (conta.tipo === "voluntario") {
    return { ...conta, ...paraPerfil(await api.meuPerfil()) }
  }
  const ongs = await api.minhasOngs()
  return { ...conta, ongs, ongId: ongs[0]?.id ?? null }
}

export function AppProvider({ children }) {
  // Incrementa após cada alteração bem-sucedida: as telas incluem
  // `versao` nas dependências de useCarregar e recarregam sozinhas.
  const [versao, setVersao] = useState(0)
  const [usuario, setUsuario] = useState(null)
  const [iniciando, setIniciando] = useState(() => api.temSessao())
  const [catalogoHabilidades, setCatalogoHabilidades] = useState([])
  const [notificacoes, setNotificacoes] = useState([])
  const [notificacoesNaoLidas, setNaoLidas] = useState(0)

  const recarregar = useCallback(() => setVersao((v) => v + 1), [])

  // Sessão salva de uma visita anterior.
  useEffect(() => {
    if (!api.temSessao()) return
    carregarUsuario()
      .then(setUsuario)
      .catch(() => api.sair())
      .finally(() => setIniciando(false))
  }, [])

  useEffect(
    () =>
      aoExpirarSessao(() => {
        setUsuario(null)
        toast.error("Sua sessão expirou. Entre novamente.")
      }),
    []
  )

  // Catálogo de habilidades (público, muda raramente): carregado uma vez.
  useEffect(() => {
    api.habilidades().then(setCatalogoHabilidades).catch(() => setCatalogoHabilidades([]))
  }, [])

  // Notificações: carga inicial + tempo real pelo WebSocket.
  const usuarioId = usuario?.id
  useEffect(() => {
    if (!usuarioId) {
      setNotificacoes([])
      setNaoLidas(0)
      return undefined
    }
    let ativo = true
    Promise.all([api.notificacoes(50), api.contarNaoLidas()])
      .then(([lista, contagem]) => {
        if (!ativo) return
        setNotificacoes(lista.map(paraNotificacao))
        setNaoLidas(contagem.nao_lidas)
      })
      .catch(() => {})
    const encerrar = conectarNotificacoes((nova) => {
      const notificacao = paraNotificacao(nova)
      setNotificacoes((atual) => [notificacao, ...atual.filter((n) => n.id !== notificacao.id)])
      setNaoLidas((n) => n + 1)
      toast.info(notificacao.titulo, { description: notificacao.mensagem })
      // A notificação indica que algo mudou no servidor (inscrição, ação).
      setVersao((v) => v + 1)
    })
    return () => {
      ativo = false
      encerrar()
    }
  }, [usuarioId])

  /** Executa uma alteração: mostra o erro do servidor ou a mensagem de
   *  sucesso e, se deu certo, faz as telas recarregarem. */
  const executar = useCallback(async (funcao, mensagemSucesso) => {
    try {
      const resultado = await funcao()
      setVersao((v) => v + 1)
      if (mensagemSucesso) toast.success(mensagemSucesso)
      return { ok: true, resultado }
    } catch (erro) {
      toast.error(erro.message)
      return { ok: false, erro: erro.message }
    }
  }, [])

  const entrar = useCallback(async (email, senha) => {
    await api.login(email, senha)
    setUsuario(await carregarUsuario())
  }, [])

  const sair = useCallback(() => {
    api.sair()
    setUsuario(null)
  }, [])

  const atualizarUsuario = useCallback(async () => {
    setUsuario(await carregarUsuario())
  }, [])

  const marcarLida = useCallback(async (id) => {
    const alvo = notificacoes.find((n) => n.id === id)
    if (!alvo || alvo.lida) return
    try {
      await api.marcarLida(id)
      setNotificacoes((atual) => atual.map((n) => (n.id === id ? { ...n, lida: true } : n)))
      setNaoLidas((n) => Math.max(n - 1, 0))
    } catch (erro) {
      toast.error(erro.message)
    }
  }, [notificacoes])

  const marcarTodasLidas = useCallback(async () => {
    try {
      await api.marcarTodasLidas()
      setNotificacoes((atual) => atual.map((n) => ({ ...n, lida: true })))
      setNaoLidas(0)
    } catch (erro) {
      toast.error(erro.message)
    }
  }, [])

  const valor = useMemo(
    () => ({
      versao,
      usuario,
      iniciando,
      catalogoHabilidades,
      notificacoes,
      notificacoesNaoLidas,
      executar,
      recarregar,
      entrar,
      sair,
      atualizarUsuario,
      marcarLida,
      marcarTodasLidas,
    }),
    [
      versao, usuario, iniciando, catalogoHabilidades, notificacoes, notificacoesNaoLidas,
      executar, recarregar, entrar, sair, atualizarUsuario, marcarLida, marcarTodasLidas,
    ]
  )

  return <AppContexto.Provider value={valor}>{children}</AppContexto.Provider>
}

export function useApp() {
  const contexto = useContext(AppContexto)
  if (!contexto) throw new Error("useApp deve ser usado dentro de AppProvider")
  return contexto
}
