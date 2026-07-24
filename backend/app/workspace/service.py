import secrets

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import Workspace
from app.workspace.dto import (
    WorkspaceCreateRequest,
)


class WorkspaceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        data: WorkspaceCreateRequest,
        owner_id: str,
    ) -> Workspace:

        existing = await self.db.scalar(
            select(Workspace).where(
                Workspace.slug == data.slug
            )
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Workspace slug already exists",
            )

        workspace = Workspace(
            id=secrets.token_hex(16),
            name=data.name,
            slug=data.slug,
            description=data.description,
            owner_id=owner_id,
        )

        self.db.add(workspace)

        await self.db.commit()
        await self.db.refresh(workspace)

        return workspace

    async def list(self, owner_id: str):

        result = await self.db.scalars(
            select(Workspace).where(
                Workspace.owner_id == owner_id
            )
        )

        return result.all()

    async def get(self, workspace_id: str):

        workspace = await self.db.scalar(
            select(Workspace).where(
                Workspace.id == workspace_id
            )
        )

        if workspace is None:
            raise HTTPException(
                status_code=404,
                detail="Workspace not found",
            )

        return workspace