import { Navigate, useLocation } from "react-router-dom"
import { Carregando } from "@/components/Carregando"
import { useApp } from "@/contexto/AppContexto"

export function RotaProtegida({ tipos, children }) {
  const { usuario, iniciando } = useApp()
  const local = useLocation()

  // Sessão salva ainda sendo validada: não redireciona para o login à toa.
  if (iniciando) return <Carregando />
  if (!usuario) {
    return <Navigate to="/entrar" replace state={{ de: local.pathname + local.search }} />
  }
  if (tipos && !tipos.includes(usuario.tipo)) {
    return <Navigate to="/painel" replace />
  }
  return children
}
