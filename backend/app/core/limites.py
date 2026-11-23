"""Limite de tentativas de login por e-mail, em memória.

Por e-mail e não por IP: atrás do proxy do Render o IP vem do
X-Forwarded-For, que o cliente consegue forjar. Contar por conta barra a
força bruta contra uma senha específica sem depender do IP.

Fica em memória do processo: serve para uma instância só (o plano
gratuito do Render) e zera quando o processo reinicia. Com mais de uma
instância, o lugar certo é um contador compartilhado (Redis ou o banco).
"""
import threading
import time
from collections import deque


class LimiteTentativas:
    def __init__(self, maximo: int, janela_segundos: int, relogio=time.monotonic):
        self.maximo = maximo
        self.janela = janela_segundos
        self._relogio = relogio
        self._falhas: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def _limpar(self, chave: str, agora: float) -> deque[float]:
        falhas = self._falhas.get(chave)
        if falhas is None:
            return deque()
        while falhas and agora - falhas[0] >= self.janela:
            falhas.popleft()
        if not falhas:
            del self._falhas[chave]
        return falhas

    def bloqueado(self, chave: str) -> bool:
        with self._lock:
            return len(self._limpar(chave, self._relogio())) >= self.maximo

    def registrar_falha(self, chave: str) -> None:
        with self._lock:
            agora = self._relogio()
            self._limpar(chave, agora)
            self._falhas.setdefault(chave, deque()).append(agora)
            # Teto de memória: muitos e-mails diferentes não crescem o dict
            # sem limite (descarta as chaves mais antigas).
            if len(self._falhas) > 10_000:
                for antiga in list(self._falhas)[:1_000]:
                    del self._falhas[antiga]

    def limpar(self, chave: str) -> None:
        with self._lock:
            self._falhas.pop(chave, None)
