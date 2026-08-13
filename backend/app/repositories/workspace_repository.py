from uuid import uuid4
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
        return result.scalars().first()

    async def get_or_create_for_user(
        self,
        user_id: str,
        user_name: str | None = None,
    ) -> Workspace:
        ws = await self.get_by_owner(user_id)
        if ws is not None:
            return ws

        ws_id = f"ws_{uuid4().hex[:16]}"
        ws_name = f"{user_name or 'User'}'s Workspace"
        slug = f"ws-{user_id[:8]}-{uuid4().hex[:6]}"
        ws = Workspace(
            id=ws_id,
            name=ws_name,
            slug=slug,
            owner_id=user_id,
            is_active=True,
        )
        self.db.add(ws)
        await self.db.commit()
        return ws