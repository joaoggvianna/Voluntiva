import { useApp } from "@/contexto/AppContexto"
import { PainelOng } from "@/pages/PainelOng"
import { PainelVoluntario } from "@/pages/PainelVoluntario"

export function Painel() {
  const { usuario } = useApp()
  // Admin usa o painel de ONG (com acesso a todas as ONGs).
  return usuario.tipo === "voluntario" ? <PainelVoluntario /> : <PainelOng />
}
