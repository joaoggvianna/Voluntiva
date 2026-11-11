import { useCallback, useEffect, useState } from "react"
import { BrowserRouter, Link, Navigate, Route, Routes, useNavigate, useParams } from "react-router-dom"
import { HeartHandshake, LogOut, MapPin, CalendarDays, Users } from "lucide-react"
import { Toaster, toast } from "sonner"
import { api, tokenStore } from "@/lib/api"

const entrada = "w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
const botao = "inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
const secundario = "inline-flex items-center justify-center rounded-md border px-4 py-2 text-sm font-medium"
const painel = "rounded-xl border bg-card p-5 shadow-sm"
const formatar = data => data ? new Date(data).toLocaleString("pt-BR", { dateStyle: "medium", timeStyle: "short" }) : ""
const mensagem = erro => erro?.message || "Não foi possível concluir a operação."

function useDados(carregar, deps) {
  const [estado, setEstado] = useState({ carregando: true, dados: null, erro: "" })
  useEffect(() => {
    let ativo = true
    setEstado({ carregando: true, dados: null, erro: "" })
    carregar().then(dados => {
      if (ativo) setEstado({ carregando: false, dados, erro: "" })
    }).catch(erro => {
      if (ativo) setEstado({ carregando: false, dados: null, erro: mensagem(erro) })
    })
    return () => { ativo = false }
  }, deps)
  return estado
}

function Aviso({ estado }) {
  if (estado.carregando) return <p role="status" className="text-muted-foreground">Carregando dados da API…</p>
  if (estado.erro) return <p role="alert" className="rounded-lg border border-destructive p-4 text-destructive">{estado.erro}</p>
  return null
}

function Cabecalho({ usuario, sair }) {
  return <header className="border-b bg-card">
    <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-5 py-4">
      <Link className="flex items-center gap-2 text-xl font-bold text-primary" to="/"><HeartHandshake/> Voluntiva</Link>
      <nav className="flex flex-wrap items-center gap-4 text-sm">
        <Link to="/acoes" className="hover:underline">Ações sociais</Link>
        {usuario && <Link to="/painel" className="hover:underline">Meu painel</Link>}
        {usuario ? <button onClick={sair} className="flex items-center gap-2 hover:underline"><LogOut size={16}/> Sair</button>
          : <Link to="/entrar" className={secundario}>Entrar</Link>}
      </nav>
    </div>
  </header>
}

function Inicio() {
  return <section className="mx-auto max-w-5xl px-5 py-20">
    <p className="mb-3 text-sm font-semibold uppercase tracking-widest text-primary">Voluntariado e impacto social</p>
    <h1 className="max-w-3xl text-4xl font-bold leading-tight md:text-5xl">Encontre uma ação social para fazer a diferença.</h1>
    <p className="mt-5 max-w-2xl text-lg text-muted-foreground">Conectamos voluntários às oportunidades publicadas por organizações sociais. Os dados exibidos vêm diretamente da plataforma.</p>
    <div className="mt-8 flex gap-3"><Link to="/acoes" className={botao}>Explorar ações</Link><Link to="/cadastro" className={secundario}>Ser voluntário</Link></div>
  </section>
}

function Autenticacao({ usuario, aoLogin, cadastro = false }) {
  const navegar = useNavigate()
  const [campos, setCampos] = useState({ nome: "", email: "", senha: "", telefone: "" })
  const [ocupado, setOcupado] = useState(false)
  if (usuario) return <Navigate to="/painel" replace />
  const mudar = (chave, valor) => setCampos(a => ({ ...a, [chave]: valor }))
  async function enviar(evento) {
    evento.preventDefault()
    setOcupado(true)
    try {
      if (cadastro) {
        await api.registrar({
          nome: campos.nome.trim(), email: campos.email.trim(),
          senha: campos.senha,
          ...(campos.telefone.trim() ? { telefone: campos.telefone.replace(/\D/g, "") } : {}),
        })
      }
      const resposta = await api.login(campos.email.trim(), campos.senha)
      tokenStore.set(resposta.access_token)
      aoLogin(resposta.usuario)
      toast.success(cadastro ? "Conta criada com sucesso!" : "Bem-vindo de volta!")
      navegar("/painel", { replace: true })
    } catch (erro) { toast.error(mensagem(erro)) } finally { setOcupado(false) }
  }
  return <section className="mx-auto max-w-md px-5 py-14">
    <div className={painel}>
      <h1 className="text-2xl font-bold">{cadastro ? "Criar conta de voluntário" : "Entrar no Voluntiva"}</h1>
      <p className="mt-2 text-sm text-muted-foreground">{cadastro ? "Cadastro conectado ao banco real. O registro de ONGs é administrado pela equipe." : "Acesse sua conta para participar ou gerenciar ações."}</p>
      <form onSubmit={enviar} className="mt-6 space-y-4">
        {cadastro && <label className="block text-sm">Nome completo<input required minLength={2} className={entrada+" mt-1"} value={campos.nome} onChange={e=>mudar("nome",e.target.value)}/></label>}
        <label className="block text-sm">E-mail<input required type="email" className={entrada+" mt-1"} value={campos.email} onChange={e=>mudar("email",e.target.value)}/></label>
        {cadastro && <label className="block text-sm">Telefone (opcional)<input className={entrada+" mt-1"} value={campos.telefone} onChange={e=>mudar("telefone",e.target.value)}/></label>}
        <label className="block text-sm">Senha<input required type="password" minLength={8} className={entrada+" mt-1"} value={campos.senha} onChange={e=>mudar("senha",e.target.value)}/></label>
        <button className={botao+" w-full"} disabled={ocupado}>{ocupado ? "Processando…" : cadastro ? "Cadastrar" : "Entrar"}</button>
      </form>
      <p className="mt-5 text-sm">{cadastro ? <>Já tem conta? <Link className="text-primary underline" to="/entrar">Entrar</Link></> : <>Ainda não tem conta? <Link className="text-primary underline" to="/cadastro">Cadastre-se</Link></>}</p>
    </div>
  </section>
}

function Acoes() {
  const [busca, setBusca] = useState("")
  const estado = useDados(() => api.listarAcoes({ status: "publicada", limite: 100 }), [])
  const acoes = (estado.dados || []).filter(acao => [acao.titulo, acao.ong_nome].join(" ").toLowerCase().includes(busca.toLowerCase()))
  return <section className="mx-auto max-w-6xl space-y-6 px-5 py-12">
    <div><h1 className="text-3xl font-bold">Ações sociais</h1><p className="mt-2 text-muted-foreground">Oportunidades publicadas pelas ONGs cadastradas.</p></div>
    <input className={entrada+" max-w-md"} placeholder="Buscar por ação ou ONG" value={busca} onChange={e=>setBusca(e.target.value)}/>
    <Aviso estado={estado}/>
    {!estado.carregando && !estado.erro && <><p className="text-sm text-muted-foreground">{acoes.length} ações encontradas</p><div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">{acoes.map(a=><article key={a.acao_id} className={painel+" space-y-3"}>
      <p className="text-xs font-semibold uppercase tracking-wide text-primary">{a.ong_nome}</p><h2 className="text-xl font-semibold">{a.titulo}</h2>
      <p className="flex items-center gap-2 text-sm text-muted-foreground"><CalendarDays size={16}/>{formatar(a.inicio)}</p>
      <p className="flex items-center gap-2 text-sm text-muted-foreground"><Users size={16}/>{a.vagas_disponiveis} vagas disponíveis</p>
      <Link to={`/acoes/${a.acao_id}`} className={secundario}>Ver detalhes</Link>
    </article>)}</div>{acoes.length===0 && <p>Nenhuma ação publicada encontrada.</p>}</>}
  </section>
}

function Detalhe({ usuario }) {
  const { id } = useParams()
  const [versao, setVersao] = useState(0)
  const [ocupado, setOcupado] = useState(false)
  const estado = useDados(() => Promise.all([api.obterAcao(id), usuario?.tipo === "voluntario" ? api.minhasInscricoes() : Promise.resolve([])]), [id, usuario?.id, versao])
  const acao = estado.dados?.[0], inscricoes = estado.dados?.[1] || []
  const inscricao = inscricoes.find(i=>i.acao_id===id && i.status!=="cancelada")
  async function alternar() {
    setOcupado(true)
    try {
      if (inscricao) await api.cancelarInscricao(id)
      else await api.inscrever(id)
      toast.success(inscricao ? "Inscrição cancelada." : "Inscrição confirmada.")
      setVersao(v=>v+1)
    } catch (erro) { toast.error(mensagem(erro)) } finally { setOcupado(false) }
  }
  return <section className="mx-auto max-w-3xl space-y-6 px-5 py-12">
    <Link to="/acoes" className="text-sm text-primary underline">Voltar às ações</Link>
    <Aviso estado={estado}/>
    {acao && <div className={painel+" space-y-5"}>
      <h1 className="text-3xl font-bold">{acao.titulo}</h1>
      <p className="whitespace-pre-line text-muted-foreground">{acao.descricao || "Sem descrição cadastrada."}</p>
      <div className="grid gap-3 text-sm sm:grid-cols-2">
        <p><CalendarDays className="mr-2 inline" size={16}/>{formatar(acao.inicio)} — {formatar(acao.fim)}</p>
        <p><MapPin className="mr-2 inline" size={16}/>{acao.local_texto || "Local a confirmar"}</p>
        <p><Users className="mr-2 inline" size={16}/>{acao.vagas} vagas totais</p>
        <p>Situação: {acao.status.replaceAll("_"," ")}</p>
      </div>
      {usuario?.tipo==="voluntario" && acao.status==="publicada" && <button className={botao} disabled={ocupado} onClick={alternar}>{ocupado ? "Processando…" : inscricao ? "Cancelar minha inscrição" : "Inscrever-me"}</button>}
      {!usuario && <p>Para participar, <Link to="/entrar" className="text-primary underline">entre na sua conta</Link>.</p>}
    </div>}
  </section>
}

function MinhasInscricoes() {
  const estado = useDados(()=>Promise.all([api.minhasInscricoes(),api.listarAcoes({status:"publicada",limite:100})]),[])
  const inscricoes = estado.dados?.[0] || []
  const mapa = new Map((estado.dados?.[1] || []).map(a=>[a.acao_id,a]))
  return <div className="space-y-4"><h2 className="text-xl font-semibold">Minhas inscrições</h2><Aviso estado={estado}/>
    {inscricoes.map(i=><div className={painel} key={i.id}><Link className="font-semibold text-primary underline" to={`/acoes/${i.acao_id}`}>{mapa.get(i.acao_id)?.titulo || "Ver ação social"}</Link><p className="mt-2 text-sm text-muted-foreground">Situação: {i.status.replaceAll("_"," ")} · Inscrito em {formatar(i.inscrito_em)}</p></div>)}
    {!estado.carregando && !estado.erro && inscricoes.length===0 && <p className="text-muted-foreground">Você ainda não se inscreveu em nenhuma ação.</p>}
  </div>
}

function GerenciarAcoes() {
  const [versao,setVersao]=useState(0)
  const [ongId,setOngId]=useState("")
  const [form,setForm]=useState({titulo:"",descricao:"",local_texto:"",inicio:"",fim:"",vagas:10,unidade_id:""})
  const [ocupado,setOcupado]=useState(false)
  const orgs=useDados(()=>api.minhasOngs(),[])
  const ongs=orgs.dados||[]
  useEffect(()=>{if(ongs.length && !ongs.some(o=>o.id===ongId))setOngId(ongs[0].id)},[orgs.dados,ongId])
  const ong=ongs.find(o=>o.id===ongId)
  const acoes=useDados(async()=>{
    if(!ongId)return []
    const estados=["rascunho","publicada","em_andamento","concluida","cancelada"]
    const grupos=await Promise.all(estados.map(status=>api.listarAcoes({status,ong_id:ongId,limite:100})))
    return grupos.flat()
  },[ongId,versao])
  function mudar(chave,valor){setForm(f=>({...f,[chave]:valor}))}
  async function criar(e){
    e.preventDefault();setOcupado(true)
    try{
      const a=await api.criarAcao({ong_id:ongId,unidade_id:form.unidade_id||null,titulo:form.titulo,descricao:form.descricao,local_texto:form.local_texto,inicio:new Date(form.inicio).toISOString(),fim:new Date(form.fim).toISOString(),vagas:Number(form.vagas),habilidades:[]})
      await api.atualizarAcao(a.id,{status:"publicada"})
      toast.success("Ação criada e publicada!")
      setForm({titulo:"",descricao:"",local_texto:"",inicio:"",fim:"",vagas:10,unidade_id:""})
      setVersao(v=>v+1)
    }catch(erro){toast.error(mensagem(erro));setVersao(v=>v+1)}finally{setOcupado(false)}
  }
  async function alterarStatus(id,status){
    try{await api.atualizarAcao(id,{status});toast.success("Situação atualizada.");setVersao(v=>v+1)}
    catch(erro){toast.error(mensagem(erro))}
  }
  return <div className="space-y-6"><h2 className="text-xl font-semibold">Gerenciar ações da ONG</h2><Aviso estado={orgs}/>
    {ong && <><label className="block max-w-md text-sm">Organização<select className={entrada+" mt-1"} value={ongId} onChange={e=>setOngId(e.target.value)}>{ongs.map(o=><option key={o.id} value={o.id}>{o.nome}</option>)}</select></label>
    <form onSubmit={criar} className={painel+" grid gap-3 md:grid-cols-2"}>
      <h3 className="text-lg font-semibold md:col-span-2">Publicar nova ação</h3>
      <label className="text-sm">Título<input required minLength={3} maxLength={160} className={entrada+" mt-1"} value={form.titulo} onChange={e=>mudar("titulo",e.target.value)}/></label>
      <label className="text-sm">Unidade (opcional)<select className={entrada+" mt-1"} value={form.unidade_id} onChange={e=>mudar("unidade_id",e.target.value)}><option value="">ONG (sem unidade)</option>{ong.unidades.map(u=><option key={u.id} value={u.id}>{u.nome} — {u.cidade}</option>)}</select></label>
      <label className="text-sm md:col-span-2">Descrição<textarea className={entrada+" mt-1"} value={form.descricao} onChange={e=>mudar("descricao",e.target.value)}/></label>
      <label className="text-sm md:col-span-2">Local<input className={entrada+" mt-1"} value={form.local_texto} onChange={e=>mudar("local_texto",e.target.value)}/></label>
      <label className="text-sm">Início<input required type="datetime-local" className={entrada+" mt-1"} value={form.inicio} onChange={e=>mudar("inicio",e.target.value)}/></label>
      <label className="text-sm">Fim<input required type="datetime-local" className={entrada+" mt-1"} value={form.fim} onChange={e=>mudar("fim",e.target.value)}/></label>
      <label className="text-sm">Vagas<input required min={1} type="number" className={entrada+" mt-1"} value={form.vagas} onChange={e=>mudar("vagas",e.target.value)}/></label>
      <div className="md:col-span-2"><button disabled={ocupado} className={botao}>{ocupado?"Salvando…":"Criar e publicar"}</button></div>
    </form>
    <h3 className="text-lg font-semibold">Ações cadastradas</h3><Aviso estado={acoes}/>
    {(acoes.dados||[]).map(a=><div className={painel+" flex flex-wrap items-center justify-between gap-3"} key={a.acao_id}>
      <div><p className="font-semibold">{a.titulo}</p><p className="text-sm text-muted-foreground">{a.status} · {formatar(a.inicio)} · {a.vagas_ocupadas}/{a.vagas} inscritos</p></div>
      <div className="flex gap-2"><Link className={secundario} to={`/acoes/${a.acao_id}`}>Detalhes</Link>{a.status==="publicada" && <button className={secundario} onClick={()=>alterarStatus(a.acao_id,"cancelada")}>Cancelar ação</button>}{a.status==="rascunho" && <button className={botao} onClick={()=>alterarStatus(a.acao_id,"publicada")}>Publicar</button>}</div>
    </div>)}</>}
    {!orgs.carregando && !orgs.erro && !ong && <p className="text-muted-foreground">Não há ONG vinculada à sua conta. O vínculo deve ser cadastrado pela administração.</p>}
  </div>
}

function Painel({ usuario }) {
  if (!usuario) return <Navigate to="/entrar" replace/>
  return <section className="mx-auto max-w-5xl space-y-7 px-5 py-12">
    <div><h1 className="text-3xl font-bold">Olá, {usuario.nome}</h1><p className="mt-2 text-muted-foreground">{usuario.tipo==="voluntario"?"Acompanhe suas inscrições e descubra novas ações.":"Gerencie as ações sociais vinculadas à sua conta."}</p></div>
    {usuario.tipo==="voluntario"? <><Link className={botao} to="/acoes">Encontrar oportunidades</Link><MinhasInscricoes/></>:<GerenciarAcoes/>}
  </section>
}

function Aplicacao() {
  const [usuario,setUsuario]=useState(null)
  const [carregando,setCarregando]=useState(true)
  const restaurar=useCallback(async()=>{
    if(!tokenStore.get()){setCarregando(false);return}
    try{setUsuario(await api.eu())}catch{tokenStore.clear();setUsuario(null)}finally{setCarregando(false)}
  },[])
  useEffect(()=>{restaurar()},[restaurar])
  function sair(){tokenStore.clear();setUsuario(null);toast.success("Você saiu da sua conta.")}
  if(carregando)return <div className="p-8 text-center">Restaurando sessão…</div>
  return <BrowserRouter><div className="flex min-h-screen flex-col">
    <Cabecalho usuario={usuario} sair={sair}/>
    <main className="flex-1"><Routes>
      <Route path="/" element={<Inicio/>}/><Route path="/acoes" element={<Acoes/>}/>
      <Route path="/acoes/:id" element={<Detalhe usuario={usuario}/>}/>
      <Route path="/entrar" element={<Autenticacao usuario={usuario} aoLogin={setUsuario}/>}/>
      <Route path="/cadastro" element={<Autenticacao usuario={usuario} aoLogin={setUsuario} cadastro/>}/>
      <Route path="/painel" element={<Painel usuario={usuario}/>}/>
      <Route path="*" element={<Navigate to="/acoes" replace/>}/>
    </Routes></main>
    <footer className="border-t px-5 py-6 text-center text-sm text-muted-foreground">Voluntiva · Gestão de voluntariado</footer>
    <Toaster richColors position="top-center"/>
  </div></BrowserRouter>
}
export default Aplicacao
