export const CAUSAS = [
  "Meio Ambiente",
  "Educação",
  "Animais",
  "Saúde",
  "Assistência Social",
  "Cultura",
  "Esporte",
  "Direitos Humanos",
]

export const UFS = [
  "AM", "BA", "CE", "DF", "MG", "PE", "PR", "RJ", "RS", "SP",
]

export const ongs = [
  {
    id: 1,
    nome: "Amigos da Floresta",
    causa: "Meio Ambiente",
    descricao:
      "ONG dedicada ao reflorestamento de áreas degradadas da Mata Atlântica e à educação ambiental em escolas públicas. Já plantamos mais de 50 mil mudas nativas com a ajuda de voluntários.",
    fundacao: 2010,
    email: "contato@amigosdafloresta.org",
    telefone: "(11) 3333-0001",
    unidades: [
      {
        id: 1,
        nome: "Sede São Paulo",
        endereco: "Rua das Palmeiras, 123 - Vila Verde",
        cidade: "São Paulo",
        uf: "SP",
        cep: "01234-001",
      },
      {
        id: 2,
        nome: "Núcleo Santos",
        endereco: "Av. da Praia Grande, 456 - Boqueirão",
        cidade: "Santos",
        uf: "SP",
        cep: "11000-002",
      },
    ],
  },
  {
    id: 2,
    nome: "EducaMais",
    causa: "Educação",
    descricao:
      "Oferecemos reforço escolar gratuito de português, matemática e inglês para crianças e adolescentes em situação de vulnerabilidade social em comunidades do Rio de Janeiro.",
    fundacao: 2015,
    email: "contato@educamais.org",
    telefone: "(21) 3333-0002",
    unidades: [
      {
        id: 3,
        nome: "Centro Comunitário Rocinha",
        endereco: "Estrada da Gávea, 789 - Rocinha",
        cidade: "Rio de Janeiro",
        uf: "RJ",
        cep: "22451-003",
      },
    ],
  },
  {
    id: 3,
    nome: "Patinhas Felizes",
    causa: "Animais",
    descricao:
      "Resgatamos, cuidamos e promovemos a adoção responsável de cães e gatos abandonados. Nosso abrigo acolhe atualmente mais de 200 animais.",
    fundacao: 2012,
    email: "contato@patinhasfelizes.org",
    telefone: "(31) 3333-0003",
    unidades: [
      {
        id: 4,
        nome: "Abrigo Central",
        endereco: "Rua dos Bichos, 321 - Santa Efigênia",
        cidade: "Belo Horizonte",
        uf: "MG",
        cep: "30110-004",
      },
    ],
  },
  {
    id: 4,
    nome: "Saúde para Todos",
    causa: "Saúde",
    descricao:
      "Levamos atendimento médico e odontológico gratuito a comunidades carentes através de mutirões de saúde com profissionais voluntários.",
    fundacao: 2018,
    email: "contato@saudeparatodos.org",
    telefone: "(71) 3333-0004",
    unidades: [
      {
        id: 5,
        nome: "Base Comunitária",
        endereco: "Largo do Pelourinho, 10 - Centro Histórico",
        cidade: "Salvador",
        uf: "BA",
        cep: "40020-005",
      },
    ],
  },
  {
    id: 5,
    nome: "Casa Acolhedora",
    causa: "Assistência Social",
    descricao:
      "Oferecemos acolhimento, alimentação e cursos profissionalizantes para pessoas em situação de rua, auxiliando na reinserção social e no mercado de trabalho.",
    fundacao: 2008,
    email: "contato@casaacolhedora.org",
    telefone: "(51) 3333-0005",
    unidades: [
      {
        id: 6,
        nome: "Casa Central",
        endereco: "Rua da Acolhida, 55 - Bom Fim",
        cidade: "Porto Alegre",
        uf: "RS",
        cep: "90030-006",
      },
      {
        id: 7,
        nome: "Anexo Canoas",
        endereco: "Av. Guilherme Schell, 200 - Centro",
        cidade: "Canoas",
        uf: "RS",
        cep: "92010-007",
      },
    ],
  },
  {
    id: 6,
    nome: "Arte nas Ruas",
    causa: "Cultura",
    descricao:
      "Promovemos oficinas gratuitas de música, teatro e artes visuais para jovens de periferia, usando a arte como ferramenta de transformação social.",
    fundacao: 2016,
    email: "contato@artenasruas.org",
    telefone: "(81) 3333-0006",
    unidades: [
      {
        id: 8,
        nome: "Galpão Cultural",
        endereco: "Rua do Bom Jesus, 180 - Recife Antigo",
        cidade: "Recife",
        uf: "PE",
        cep: "50030-008",
      },
    ],
  },
  {
    id: 7,
    nome: "Esporte que Transforma",
    causa: "Esporte",
    descricao:
      "Usamos o esporte como ferramenta de inclusão social, oferecendo treinos gratuitos de futebol, vôlei e judô para crianças e adolescentes.",
    fundacao: 2014,
    email: "contato@esportetransforma.org",
    telefone: "(41) 3333-0007",
    unidades: [
      {
        id: 9,
        nome: "Centro Esportivo Boqueirão",
        endereco: "Rua Inácio Lustosa, 300 - Boqueirão",
        cidade: "Curitiba",
        uf: "PR",
        cep: "81710-009",
      },
    ],
  },
  {
    id: 8,
    nome: "Direitos Iguais",
    causa: "Direitos Humanos",
    descricao:
      "Oferecemos orientação jurídica gratuita e promovemos a defesa dos direitos de populações vulneráveis, incluindo idosos, imigrantes e vítimas de violência.",
    fundacao: 2011,
    email: "contato@direitosiguais.org",
    telefone: "(61) 3333-0008",
    unidades: [
      {
        id: 10,
        nome: "Escritório Central",
        endereco: "SQS 308 Bloco C, 100 - Asa Sul",
        cidade: "Brasília",
        uf: "DF",
        cep: "70300-010",
      },
    ],
  },
]
