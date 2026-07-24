from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import Workspace


class WorkspaceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_owner(
        self,
        owner_id: str,
    ) -> Workspace | None:

        result = await self.db.execute(
            select(Workspace).where(
                Workspace.owner_id == owner_id,
                Workspace.is_active.is_(True),
            )
        )

        return result.scalar_one_or_none()