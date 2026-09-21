import { useState } from "react"
import { Link, NavLink, useNavigate } from "react-router-dom"
import { HeartHandshake, LayoutDashboard, LogOut, Menu, X } from "lucide-react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { SinoNotificacoes } from "@/components/SinoNotificacoes"
import { useApp } from "@/contexto/AppContexto"
import { sair } from "@/lib/servico"

const links = [
  { to: "/", label: "Início", fim: true },
  { to: "/acoes", label: "Ações sociais" },
  { to: "/ongs", label: "ONGs" },
]

function iniciais(nome) {
  return nome
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((parte) => parte[0].toUpperCase())
    .join("")
}

function classeLink({ isActive }) {
  return `text-sm font-medium transition-colors hover:text-primary ${
    isActive ? "text-primary" : "text-muted-foreground"
  }`
}

export function Navbar() {
  const [aberto, setAberto] = useState(false)
  const { usuario, executar } = useApp()
  const navegar = useNavigate()

  function sairDaConta() {
    executar(() => sair(), "Você saiu da sua conta.")
    setAberto(false)
    navegar("/")
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <Link to="/" className="flex items-center gap-2 text-lg font-bold">
          <HeartHandshake className="h-7 w-7 text-primary" />
          <span>
            Volunti<span className="text-primary">va</span>
          </span>
        </Link>

        <nav className="hidden items-center gap-6 md:flex">
          {links.map((link) => (
            <NavLink key={link.to} to={link.to} end={link.fim} className={classeLink}>
              {link.label}
            </NavLink>
          ))}
        </nav>

        <div className="hidden items-center gap-2 md:flex">
          {usuario ? (
            <>
              <SinoNotificacoes />
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="gap-2 px-2">
                    <Avatar className="h-8 w-8">
                      <AvatarFallback className="bg-primary/10 text-xs font-semibold text-primary">
                        {iniciais(usuario.nome)}
                      </AvatarFallback>
                    </Avatar>
                    <span className="max-w-32 truncate text-sm">{usuario.nome}</span>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel className="space-y-0.5">
                    <p className="truncate">{usuario.nome}</p>
                    <p className="truncate text-xs font-normal text-muted-foreground">
                      {usuario.tipo === "ong" ? "Conta de ONG" : "Conta de voluntário"}
                    </p>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link to="/painel">
                      <LayoutDashboard className="mr-2 h-4 w-4" /> Meu painel
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem onSelect={sairDaConta}>
                    <LogOut className="mr-2 h-4 w-4" /> Sair
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </>
          ) : (
            <>
              <Button asChild variant="ghost">
                <Link to="/entrar">Entrar</Link>
              </Button>
              <Button asChild>
                <Link to="/cadastro">Criar conta</Link>
              </Button>
            </>
          )}
        </div>

        <div className="flex items-center gap-1 md:hidden">
          {usuario && <SinoNotificacoes />}
          <button
            className="p-2"
            onClick={() => setAberto(!aberto)}
            aria-label={aberto ? "Fechar menu" : "Abrir menu"}
          >
            {aberto ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>
      </div>

      {aberto && (
        <nav className="flex flex-col gap-3 border-t bg-background px-4 py-4 md:hidden">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.fim}
              onClick={() => setAberto(false)}
              className={classeLink}
            >
              {link.label}
            </NavLink>
          ))}
          {usuario ? (
            <>
              <NavLink to="/painel" onClick={() => setAberto(false)} className={classeLink}>
                Meu painel
              </NavLink>
              <Button variant="outline" onClick={sairDaConta}>
                <LogOut /> Sair
              </Button>
            </>
          ) : (
            <div className="grid grid-cols-2 gap-2">
              <Button asChild variant="outline">
                <Link to="/entrar" onClick={() => setAberto(false)}>
                  Entrar
                </Link>
              </Button>
              <Button asChild>
                <Link to="/cadastro" onClick={() => setAberto(false)}>
                  Criar conta
                </Link>
              </Button>
            </div>
          )}
        </nav>
      )}
    </header>
  )
}
