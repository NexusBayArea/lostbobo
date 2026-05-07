import pytest
from unittest.mock import AsyncMock, patch

from backend.core.extractor.claim_extractor import ClaimExtractor, ClaimExtractionResult


@pytest.fixture
def extractor():
    return ClaimExtractor()


@pytest.mark.asyncio
async def test_claim_extractor_primary_success(extractor):
    llm_output = '{"hypothesis": "Valid claim", "confidence": 0.9}'

    with patch.object(
        extractor, "_parse_llm_output", new_callable=AsyncMock
    ) as mock_parse:
        mock_parse.return_value = ClaimExtractionResult(
            hypothesis="Valid claim",
            raw_output=llm_output,
            confidence=0.9,
            degraded=False,
        )

        result = await extractor.extract(llm_output)

    assert not result.degraded
    assert result.confidence == 0.9
    assert result.hypothesis == "Valid claim"


@pytest.mark.asyncio
async def test_claim_extractor_regex_fallback(extractor):
    """Malformed JSON → regex fallback."""
    bad_output = "Some unstructured text with hypothesis: 'Energy density improved'"

    with patch.object(
        extractor, "_parse_llm_output", side_effect=Exception("JSON parse error")
    ):
        with patch.object(extractor, "_regex_fallback_parser") as mock_regex:
            mock_regex.return_value = ["Energy density improved"]
            with patch.object(extractor, "_default_template_claims", return_value=[]):
                result = await extractor.extract(bad_output)

    assert result.degraded is True
    assert result.fallback_used == ["regex_parser"]
    assert "Energy density improved" in result.hypothesis


@pytest.mark.asyncio
async def test_claim_extractor_full_fallback_to_template(extractor):
    """Regex also fails → default template."""
    bad_output = "completely unparseable"

    with patch.object(extractor, "_parse_llm_output", side_effect=Exception("fail")):
        with patch.object(extractor, "_regex_fallback_parser", return_value=[]):
            with patch.object(extractor, "_default_template_claims") as mock_template:
                mock_template.return_value = ["Default physics hypothesis"]

                result = await extractor.extract(bad_output)

    assert result.degraded is True
    assert result.fallback_used == ["regex_parser"]
    assert "Default physics hypothesis" in result.hypothesis
    assert result.confidence <= 0.55
