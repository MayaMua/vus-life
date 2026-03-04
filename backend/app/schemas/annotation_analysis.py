from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional

# --- 1. Define the Desired Output Structure (Pydantic) ---
class FinalVerdict(str, Enum):
    """Enumeration of possible final verdicts"""
    LIKELY_PATHOGENIC = "Likely Pathogenic"
    VUS = "VUS"
    LIKELY_BENIGN = "Likely Benign"
    BENIGN = "Benign"


class VariantAnalysis(BaseModel):
    """Structured output from the Clinical Reasoning Agent"""
    mechanism_analysis: str = Field(
        description="Detailed analysis of how the target variant compares biologically to neighbors. "
        "Focus on functional impact, amino acid changes, and whether the mechanism matches."
    )
    score_concordance: str = Field(
        description="Analysis of whether computational scores (AlphaMissense, EVE, SpliceAI) align "
        "between target and neighbors. Highlight any significant discrepancies."
    )
    red_flags: List[str] = Field(
        description="Specific reasons to doubt the embedding model's prediction. "
        "Examples: 'Target AlphaMissense is low (0.2) while neighbors are high (>0.9)', "
        "'Target has conservative amino acid change while neighbors have radical changes'."
    )
    final_verdict: FinalVerdict = Field(
        description="Final classification recommendation based on the discordance analysis"
    )
    confidence: float = Field(
        description="Confidence score in this assessment, ranging from 0.0 to 1.0",
        ge=0.0,
        le=1.0
    )
    prediction_agreement: Optional[str] = Field(
        default=None,
        description="Comparison with VUS_LIFE prediction: 'Matching' if agent verdict aligns with "
        "VUS_LIFE prediction, 'Conflicting' if they disagree. None if no prediction available."
    )