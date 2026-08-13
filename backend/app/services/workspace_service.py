import secrets

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import Workspace


class WorkspaceService:

    async def create_default_workspace(
        self,
        db: AsyncSession,
        owner_id: str,
        owner_name: str,
    ) -> Workspace:

        slug = (
            owner_name.lower()
            .replace(" ", "-")
            + "-"
            + secrets.token_hex(3)
        )

        workspace = Workspace(
            id=secrets.token_hex(16),
            name=f"{owner_name}'s Workspace",
            slug=slug,
            owner_id=owner_id,
        )

        db.add(workspace)

        await db.commit()

        return workspace


workspace_service = WorkspaceService()