"""Backward-compatible KSPP API. Prefer ``QEInput.KSPPResolver`` and ``QEInput.apply_kspp``."""

from .io import KSPPNotFoundError, QEInput

KSPPResolver = QEInput.KSPPResolver


def apply_kspp(*args, **kwargs):
    return QEInput.apply_kspp(*args, **kwargs)


__all__ = ["KSPPResolver", "apply_kspp", "KSPPNotFoundError"]
