import { createContext, useCallback, useContext, useMemo, useState } from "react"
import { toast } from "sonner"
import { iniciarBanco } from "@/lib/armazenamento"
import * as servico from "@/lib/servico"

iniciarBanco()

const AppContexto = createContext(null)

export function AppProvider({ children }) {
  const [versao, setVersao] = useState(0)

  const recarregar = useCallback(() => setVersao((v) => v + 1), [])

  const executar = useCallback(
    (funcao, mensagemSucesso) => {
      try {
        const resultado = funcao()
        recarregar()
        if (mensagemSucesso) toast.success(mensagemSucesso)
        return { ok: true, resultado }
      } catch (erro) {
        toast.error(erro.message)
        return { ok: false, erro: erro.message }
      }
    },
    [recarregar]
  )

  const valor = useMemo(() => {
    const usuario = servico.usuarioAtual()
    return {
      versao,
      usuario,
      executar,
      recarregar,
      notificacoesNaoLidas: usuario
        ? servico.listarNotificacoes(usuario.id).filter((n) => !n.lida).length
        : 0,
    }
  }, [versao, executar, recarregar])

  return <AppContexto.Provider value={valor}>{children}</AppContexto.Provider>
}

export function useApp() {
  const contexto = useContext(AppContexto)
  if (!contexto) throw new Error("useApp deve ser usado dentro de AppProvider")
  return contexto
}
