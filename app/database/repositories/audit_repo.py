"""Audit repository for compliance and tracking administrative operations."""

from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.audit_log import AuditLog


class AuditRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_action(
        self,
        actor_telegram_id: int,
        action: str,
        target_type: str,
        target_id: str | int,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Create an audit log record."""
        log_entry = AuditLog(
            actor_telegram_id=actor_telegram_id,
            action=action,
            target_type=target_type,
            target_id=str(target_id),
            metadata_payload=metadata or {},
        )
        self.session.add(log_entry)
        await self.session.flush()
        return log_entry
