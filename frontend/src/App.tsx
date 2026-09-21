import { AuthProvider, useAuth } from '@/context/AuthContext'
import { Layout } from '@/components/Layout'
import { Login } from '@/pages/Login'
import { Acoes } from '@/pages/Acoes'

function Conteudo() {
  const { usuario, carregando } = useAuth()
  if (carregando) return <p className="p-6 text-ink-muted">Carregando...</p>
  return <Layout>{usuario ? <Acoes /> : <Login />}</Layout>
}

// TODO(equipe): trocar por react-router quando houver mais de duas telas.
// O pacote já está instalado; faltam as rotas de cadastro, perfil,
// histórico do voluntário e painel da ONG.
export default function App() {
  return (
    <AuthProvider>
      <Conteudo />
    </AuthProvider>
  )
}
