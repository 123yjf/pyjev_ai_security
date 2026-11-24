"""Compatibility names for callers of the original source-only interface."""
from pyjev import Auditor
from pyjev_v1 import Auditor as ScopeAuditor, Decision, audit
from pyjev_v1._engine import reference_only

VERSION = "scope-1"  # Historical identifier, preserved only for existing source integrations.
