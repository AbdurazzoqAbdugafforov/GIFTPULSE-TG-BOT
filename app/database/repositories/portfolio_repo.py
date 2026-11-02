"""Portfolio and PortfolioPosition repository for GiftPulse."""

from decimal import Decimal
from typing import Optional
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database.models.portfolio import Portfolio, PortfolioPosition


class PortfolioRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_portfolio(self, user_id: int) -> Portfolio:
        """Fetch or create default user portfolio."""
        stmt = (
            select(Portfolio)
            .where(Portfolio.user_id == user_id)
            .options(selectinload(Portfolio.positions))
        )
        result = await self.session.execute(stmt)
        portfolio = result.scalar_one_or_none()
        if portfolio:
            return portfolio

        portfolio = Portfolio(user_id=user_id, name="Main Portfolio")
        self.session.add(portfolio)
        await self.session.flush()
        return portfolio

    async def get_positions(self, user_id: int) -> list[PortfolioPosition]:
        """Fetch all positions belonging to user."""
        portfolio = await self.get_or_create_portfolio(user_id)
        stmt = (
            select(PortfolioPosition)
            .where(PortfolioPosition.portfolio_id == portfolio.id)
            .options(
                selectinload(PortfolioPosition.collection),
                selectinload(PortfolioPosition.model),
            )
            .order_by(PortfolioPosition.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add_position(
        self,
        user_id: int,
        collection_id: int,
        quantity: Decimal,
        purchase_price: Decimal,
        model_id: Optional[int] = None,
        purchase_date: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> PortfolioPosition:
        """Add new position to user portfolio."""
        portfolio = await self.get_or_create_portfolio(user_id)
        pos = PortfolioPosition(
            portfolio_id=portfolio.id,
            collection_id=collection_id,
            model_id=model_id,
            quantity=quantity,
            purchase_price=purchase_price,
            purchase_date=purchase_date,
            notes=notes,
        )
        self.session.add(pos)
        await self.session.flush()
        return pos

    async def delete_position(self, user_id: int, position_id: int) -> bool:
        """Delete position owned by user."""
        portfolio = await self.get_or_create_portfolio(user_id)
        stmt = (
            delete(PortfolioPosition)
            .where(
                PortfolioPosition.id == position_id,
                PortfolioPosition.portfolio_id == portfolio.id,
            )
        )
        res = await self.session.execute(stmt)
        await self.session.flush()
        return res.rowcount > 0
