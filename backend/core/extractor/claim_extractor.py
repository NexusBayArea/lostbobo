"""Claim Extractor — Structured LLM Output → Hypothesis.

Part of the Deterministic Cascade: extract → validate → simulate
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field

from backend.core.models.hypothesis import Hypothesis

log = logging.getLogger(__name__)


class ExtractedClaim(BaseModel):
    """Structured claim parsed from LLM output"""

    claim: str
    reasoning: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    domain: str = "general"
    simulation_type: str | None = None
    units: dict[str, str] = Field(default_factory=dict)


@dataclass
class ClaimExtractionResult:
    hypothesis: Hypothesis
    raw_llm_output: str
    extraction_confidence: float
    parsing_success: bool


class ClaimExtractor:
    """Parses raw LLM output into structured claims + simulation-ready parameters."""

    async def extract(self, llm_output: str, query: str = "") -> ClaimExtractionResult:
        """Main entry point."""
        try:
            structured = await self._parse_llm_output(llm_output, query)

            hyp = Hypothesis(
                claim={
                    "text": structured.claim,
                    "domain": structured.domain,
                    "simulation_type": structured.simulation_type,
                },
                reasoning=structured.reasoning,
                sim_params=structured.parameters,
                trust_score=structured.confidence * 0.6,
                stage="extracted",
            )

            return ClaimExtractionResult(
                hypothesis=hyp,
                raw_llm_output=llm_output,
                extraction_confidence=structured.confidence,
                parsing_success=True,
            )

        except Exception as e:
            log.error(f"Claim extraction failed: {e}")
            fallback = Hypothesis(
                claim={"text": llm_output[:500], "domain": "unknown"},
                reasoning="Extraction failed — raw output preserved",
                stage="extraction_failed",
            )
            return ClaimExtractionResult(
                hypothesis=fallback,
                raw_llm_output=llm_output,
                extraction_confidence=0.0,
                parsing_success=False,
            )

    async def _parse_llm_output(self, text: str, query: str) -> ExtractedClaim:
        """Intelligent parsing with multiple strategies."""
        text = text.strip()

        try:
            if "```json" in text:
                json_block = text.split("```json")[1].split("```")[0]
            elif "{" in text and "}" in text:
                json_block = text[text.find("{") : text.rfind("}") + 1]
            else:
                raise ValueError("No JSON found")

            data = json.loads(json_block)

            return ExtractedClaim(
                claim=data.get("claim") or data.get("statement") or query,
                reasoning=data.get("reasoning", ""),
                parameters=data.get("parameters") or data.get("params", {}),
                confidence=data.get("confidence", 0.75),
                domain=data.get("domain", "general"),
                simulation_type=data.get("simulation_type"),
                units=data.get("units", {}),
            )
        except Exception:
            pass

        claim = text.split("\n")[0].strip("#* -")
        params = {}

        for line in text.split("\n"):
            line = line.strip()
            if ":" in line and not line.startswith("http"):
                key, val = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                params[key] = val.strip()

        return ExtractedClaim(
            claim=claim or query,
            reasoning=text,
            parameters=params,
            confidence=0.65,
            domain="general",
        )


_claim_extractor: ClaimExtractor | None = None


def get_claim_extractor() -> ClaimExtractor:
    global _claim_extractor
    if _claim_extractor is None:
        _claim_extractor = ClaimExtractor()
    return _claim_extractor
