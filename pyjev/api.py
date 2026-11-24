"""Typed, deterministic post-response annotation. No authority to execute, notify, or block."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from hashlib import sha256
from importlib.resources import files
import json
from typing import Literal
from ._detector import Detector, LIMIT
from ._intent import Head, disposition

Signal = Literal["suspected", "no_signal", "unknown"]
SpeechAct = Literal["mention", "act", "unclear"]
Route = Literal["review", "record_only", "no_signal", "incomplete"]
DefaultRoute = Literal["review", "no_signal", "incomplete"]
_DIGESTS = {
    "rulebook.json": "d98dd4e58ec4670abaea9fd32c42adef73048bcc07b1e7b6b7e7a37e13a2ec42",
    "head.json": "9bbc915995945b5cbf3f4e2f9ef35254ac00e331b1896e2ebf15a27e84661ded",
    "results.json": "d4e354aa67fe216611aeb609de62a6314389a5fba843fdee1a33f1466891d037",
    "pybot-raw-control.json": "3dad36fe2534a6c7e43690abaf84b31a7fbb273cf2b52de35df369c38d618456",
    "pybot-comparison.json": "c629a8547e81c7a45eedd740dc9393b7df9403df71601ce20ef180ee91d719d0",
}

class ModelIntegrityError(RuntimeError):
    """Bundled asset missing or changed; callers must not treat this as no_signal."""

def _read(name: str) -> dict:
    try:
        raw = files("pyjev").joinpath("data").joinpath(name).read_bytes()
        if sha256(raw).hexdigest() != _DIGESTS[name]:
            raise ModelIntegrityError("Asset checksum mismatch: " + name)
        return json.loads(raw)
    except (KeyError, OSError, ValueError) as exc:
        raise ModelIntegrityError("Cannot load bundled asset: " + name) from exc

@dataclass(frozen=True, slots=True)
class Audit:
    signal: Signal
    speech_act: SpeechAct
    review: DefaultRoute
    experimental_review: Route
    execution_evidence: Literal["not_observed"] = field(default="not_observed", init=False)
    grants_authority: Literal[False] = field(default=False, init=False)
    service_action: Literal["none"] = field(default="none", init=False)
    schema_version: Literal[1] = field(default=1, init=False)

    def as_dict(self) -> dict:
        """JSON-serializable; never includes the submitted text or a model confidence."""
        return asdict(self)

@lru_cache(maxsize=1)
def _models() -> tuple[Detector, Head]:
    return Detector.parse(_read("rulebook.json")), Head(_read("head.json"))

class Auditor:
    """Load verified local weights once; audit each text independently."""
    def __init__(self) -> None:
        self._base, self._head = _models()

    def audit(self, text: str) -> Audit:
        if not isinstance(text, str) or len(text) > LIMIT or not text.strip():
            return Audit("unknown", "unclear", "incomplete", "incomplete")
        # Lone UTF-16 surrogates are not Unicode scalar values.
        if any(0xD800 <= ord(c) <= 0xDFFF for c in text):
            return Audit("unknown", "unclear", "incomplete", "incomplete")
        evidence = self._base.evidence(text)
        if evidence is None:
            return Audit("unknown", "unclear", "incomplete", "incomplete")
        raw = bool(evidence[-1])
        act = self._head.state(text)
        return Audit("suspected" if raw else "no_signal", act,
                     "review" if raw else "no_signal", disposition(raw, act))

def audit(text: str) -> Audit:
    """Audit a single text; shares the read-only model cache across calls."""
    return Auditor().audit(text)
