import { useEffect } from "react"
import { BrowserRouter, Route, Routes, useLocation } from "react-router-dom"
import { Toaster } from "@/components/ui/sonner"
import { Navbar } from "@/components/layout/Navbar"
import { Footer } from "@/components/layout/Footer"
import { RotaProtegida } from "@/components/RotaProtegida"
import { AppProvider } from "@/contexto/AppContexto"
import { Home } from "@/pages/Home"
import { Acoes } from "@/pages/Acoes"
import { AcaoDetalhe } from "@/pages/AcaoDetalhe"
import { Ongs } from "@/pages/Ongs"
import { OngDetalhe } from "@/pages/OngDetalhe"
import { Entrar } from "@/pages/Entrar"
import { Cadastro } from "@/pages/Cadastro"
import { Painel } from "@/pages/Painel"
import { NaoEncontrada } from "@/pages/NaoEncontrada"

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
          </main>
          <Footer />
          <Toaster richColors position="top-center" />
        </div>
      </BrowserRouter>
    </AppProvider>
  )
}

export default App
