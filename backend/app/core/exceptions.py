"""Exceções de domínio.

Os serviços levantam estas — nunca HTTPException. Assim a mesma regra de
negócio serve à API REST e ao servidor TCP, que traduzem cada exceção
para o seu próprio formato de erro.
"""


class VoluntivaError(Exception):
    """Base de todos os erros de domínio."""
    codigo = "erro_interno"

    def __init__(self, mensagem: str):
        super().__init__(mensagem)
        self.mensagem = mensagem


class CredenciaisInvalidas(VoluntivaError):
    codigo = "credenciais_invalidas"


class UsuarioInativo(VoluntivaError):
    codigo = "usuario_inativo"


class RecursoNaoEncontrado(VoluntivaError):
    codigo = "nao_encontrado"


class ConflitoDeEstado(VoluntivaError):
    """Ex.: já inscrito, ação lotada, presença sem inscrição confirmada."""
    codigo = "conflito"


class PermissaoNegada(VoluntivaError):
    codigo = "permissao_negada"


class DadosInvalidos(VoluntivaError):
    codigo = "dados_invalidos"
