from pydantic import BaseModel, ConfigDict


class WorkspaceCreateRequest(BaseModel):
    name: str
    slug: str
    description: str | None = None


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    description: str | None
    owner_id: str
    is_active: bool