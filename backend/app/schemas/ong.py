"""Schemas de ONG e unidade."""
import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models.enums import CausaSocial

_UF = r"^[A-Z]{2}$"
_CEP = r"^[0-9]{8}$"
_TELEFONE = r"^[0-9]{10,13}$"


class UnidadeCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=160)
    cep: str | None = Field(default=None, pattern=_CEP)
    logradouro: str | None = Field(default=None, max_length=200)
    numero: str | None = Field(default=None, max_length=20)
    complemento: str | None = Field(default=None, max_length=100)
    bairro: str | None = Field(default=None, max_length=100)
    cidade: str = Field(min_length=2, max_length=120)
    uf: str = Field(pattern=_UF)


class UnidadeUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=160)
    cep: str | None = Field(default=None, pattern=_CEP)
    logradouro: str | None = Field(default=None, max_length=200)
    numero: str | None = Field(default=None, max_length=20)
    complemento: str | None = Field(default=None, max_length=100)
    bairro: str | None = Field(default=None, max_length=100)
    cidade: str | None = Field(default=None, min_length=2, max_length=120)
    uf: str | None = Field(default=None, pattern=_UF)


class UnidadeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ong_id: uuid.UUID
    nome: str
    cep: str | None
    logradouro: str | None
    numero: str | None
    complemento: str | None
    bairro: str | None
    cidade: str
    uf: str


class OngCadastro(BaseModel):
    """Cadastro público de ONG: cria a ONG, a conta de acesso (tipo ong),
    o vínculo de proprietário e, se houver endereço, a unidade "Sede"."""
    nome: str = Field(min_length=2, max_length=160)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)
    # Nome da pessoa responsável pela conta; sem ele, usa o nome da ONG.
    nome_responsavel: str | None = Field(default=None, min_length=2, max_length=120)
    cnpj: str | None = Field(default=None, pattern=r"^[0-9]{14}$")
    telefone: str | None = Field(default=None, pattern=_TELEFONE)
    descricao: str | None = Field(default=None, max_length=5000)
    site: str | None = Field(default=None, pattern=r"^https?://", max_length=300)
    causa: CausaSocial | None = None
    sede: UnidadeCreate | None = None


class OngUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=160)
    email_contato: EmailStr | None = None
    telefone: str | None = Field(default=None, pattern=_TELEFONE)
    descricao: str | None = Field(default=None, max_length=5000)
    site: str | None = Field(default=None, pattern=r"^https?://", max_length=300)
    causa: CausaSocial | None = None

    @model_validator(mode="after")
    def _nome_nao_nulo(self):
        if "nome" in self.model_fields_set and self.nome is None:
            raise ValueError("nome não pode ser vazio")
        return self


class OngPublica(BaseModel):
    """GET /ongs e /ongs/{id}. CNPJ e e-mail de login não são expostos."""
    id: uuid.UUID
    nome: str
    descricao: str | None
    site: str | None
    email_contato: str | None
    telefone: str | None
    causa: CausaSocial | None
    unidades: list[UnidadeResponse]
    acoes_abertas: int


class UnidadeResumo(BaseModel):
    id: uuid.UUID
    nome: str
    cidade: str
    uf: str


class MinhaOng(BaseModel):
    """GET /ongs/minhas: ONGs que o usuário gere e as unidades a que tem acesso."""
    id: uuid.UUID
    nome: str
    acesso_total: bool
    papel: str | None
    unidades: list[UnidadeResumo]
