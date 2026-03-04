from pathlib import Path
from pydantic import BaseModel, Field

class GeneralSettings(BaseModel):
    """General app settings (e.g. output path, agreement)."""

    output_path: str = Field(
        default_factory=lambda: str(Path.home() / "Documents"),
        description="Data output directory path",
    )
    has_accepted_agreement: bool = Field(
        default=False,
        description="Whether user has accepted the data usage agreement",
    )
