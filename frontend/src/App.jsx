import { lazy, Suspense, useEffect } from "react"
import { BrowserRouter, Route, Routes, useLocation } from "react-router-dom"
import { Toaster } from "@/components/ui/sonner"
import { Carregando } from "@/components/Carregando"
import { Navbar } from "@/components/layout/Navbar"
import { Footer } from "@/components/layout/Footer"
import { RotaProtegida } from "@/components/RotaProtegida"
import { AppProvider } from "@/contexto/AppContexto"
import { Home } from "@/pages/Home"

// Demais páginas carregadas sob demanda: a página inicial não baixa o
// código dos painéis, formulários e tabelas que o visitante nem abriu.
const porNome = (carregar, nome) => lazy(() => carregar().then((m) => ({ default: m[nome] })))
const Acoes = porNome(() => import("@/pages/Acoes"), "Acoes")
const AcaoDetalhe = porNome(() => import("@/pages/AcaoDetalhe"), "AcaoDetalhe")
const Ongs = porNome(() => import("@/pages/Ongs"), "Ongs")
const OngDetalhe = porNome(() => import("@/pages/OngDetalhe"), "OngDetalhe")
const Entrar = porNome(() => import("@/pages/Entrar"), "Entrar")
const Cadastro = porNome(() => import("@/pages/Cadastro"), "Cadastro")
const Painel = porNome(() => import("@/pages/Painel"), "Painel")
const NaoEncontrada = porNome(() => import("@/pages/NaoEncontrada"), "NaoEncontrada")

function RolarParaTopo() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])
  return null
}

function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <RolarParaTopo />
        <div className="flex min-h-screen flex-col">
          <Navbar />
          <main className="flex-1">
            <Suspense fallback={<Carregando />}>
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/acoes" element={<Acoes />} />
                <Route path="/acoes/:id" element={<AcaoDetalhe />} />
                <Route path="/ongs" element={<Ongs />} />
                <Route path="/ongs/:id" element={<OngDetalhe />} />
                <Route path="/entrar" element={<Entrar />} />
                <Route path="/cadastro" element={<Cadastro />} />
                <Route
                  path="/painel"
                  element={
                    <RotaProtegida>
                      <Painel />
                    </RotaProtegida>
                  }
                />
                <Route path="*" element={<NaoEncontrada />} />
              </Routes>
            </Suspense>
          </main>
          <Footer />
          <Toaster richColors position="top-center" />
        </div>
      </BrowserRouter>
    </AppProvider>
  )
}

export default App
