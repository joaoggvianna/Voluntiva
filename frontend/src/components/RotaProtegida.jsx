import { Navigate, useLocation } from "react-router-dom"
import { useApp } from "@/contexto/AppContexto"

export function RotaProtegida({ tipos, children }) {
  const { usuario } = useApp()
  const local = useLocation()

  if (!usuario) {
    return <Navigate to="/entrar" replace state={{ de: local.pathname + local.search }} />
  }
  if (tipos && !tipos.includes(usuario.tipo)) {
    return <Navigate to="/painel" replace />
  }
  return children
}
