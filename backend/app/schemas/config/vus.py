from pydantic import BaseModel, Field

class VusApiSettings(BaseModel):
    api_url: str = "http://vus.life/api"

class VusDashboardSettings(BaseModel):
    gene_names: list[str] = Field(default_factory=list)
    embedding_models: list[str] = Field(default_factory=list)
    annotation_methods: list[str] = Field(default_factory=list)