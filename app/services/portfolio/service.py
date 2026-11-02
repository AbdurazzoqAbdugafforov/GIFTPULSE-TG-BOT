"""Portfolio service for manual Gift holdings valuation and PnL analytics."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.constants import DATA_ATTRIBUTION_TEXT, DATA_ATTRIBUTION_URL, MARKET_DISCLAIMER
from app.database.models.collection import CollectionFloorSnapshot, GiftCollection
from app.database.models.model_item import GiftModel, ModelFloorSnapshot
from app.database.models.portfolio import Portfolio, PortfolioPosition


class PortfolioService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_default_portfolio(self, user_id: int) -> Portfolio:
        """Fetch or create user's default portfolio."""
        stmt = select(Portfolio).where(Portfolio.user_id == user_id).order_by(Portfolio.created_at.asc()).limit(1)
        res = await self.session.execute(stmt)
        portfolio = res.scalar_one_or_none()
        if not portfolio:
            portfolio = Portfolio(user_id=user_id, name="Main Portfolio")
            self.session.add(portfolio)
            await self.session.commit()
        return portfolio

    async def add_position(
        self,
        portfolio_id: int,
        collection_id: int,
        quantity: Decimal,
        purchase_price: Decimal,
        model_id: Optional[int] = None,
        purchase_date: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> PortfolioPosition:
        """Add a manually tracked gift position to portfolio."""
        pos = PortfolioPosition(
            portfolio_id=portfolio_id,
            collection_id=collection_id,
            model_id=model_id,
            quantity=quantity,
            purchase_price=purchase_price,
            purchase_date=purchase_date,
            notes=notes,
        )
        self.session.add(pos)
        await self.session.commit()
        return pos

    async def delete_position(self, position_id: int, user_id: int) -> bool:
        """Delete position with ownership check."""
        stmt = (
            select(PortfolioPosition)
            .join(Portfolio)
            .where(PortfolioPosition.id == position_id, Portfolio.user_id == user_id)
        )
        res = await self.session.execute(stmt)
        pos = res.scalar_one_or_none()
        if pos:
            await self.session.delete(pos)
            await self.session.commit()
            return True
        return False

    async def calculate_summary(self, user_id: int, portfolio_id: Optional[int] = None) -> dict[str, Any]:
        """Calculate estimated portfolio value, profit/loss, and asset allocation with clear warnings."""
        if not portfolio_id:
            port = await self.get_or_create_default_portfolio(user_id)
            portfolio_id = port.id

        stmt = (
            select(PortfolioPosition)
            .where(PortfolioPosition.portfolio_id == portfolio_id)
            .options(
                selectinload(PortfolioPosition.collection),
                selectinload(PortfolioPosition.model),
            )
        )
        res = await self.session.execute(stmt)
        positions = list(res.scalars().all())

        if not positions:
            return {
                "portfolio_id": portfolio_id,
                "total_estimated_value": 0.0,
                "total_cost_basis": 0.0,
                "total_unrealized_pnl": 0.0,
                "total_pnl_pct": 0.0,
                "currency": "GRAM",
                "positions": [],
                "distribution": [],
                "warnings": [],
                "disclaimer": MARKET_DISCLAIMER,
                "attribution": DATA_ATTRIBUTION_TEXT,
                "attribution_url": DATA_ATTRIBUTION_URL,
            }

        total_cost = Decimal("0.0")
        total_estimated = Decimal("0.0")
        pos_summaries = []
        warnings = []
        col_distribution: dict[str, Decimal] = {}

        for p in positions:
            cost = p.quantity * p.purchase_price
            total_cost += cost

            # Determine floor valuation basis
            estimated_floor = None
            valuation_source = "COLLECTION_FLOOR"
            pos_warning = None

            # 1. Try model floor first if model is specified
            if p.model_id:
                m_snap_stmt = (
                    select(ModelFloorSnapshot)
                    .where(ModelFloorSnapshot.model_id == p.model_id)
                    .order_by(ModelFloorSnapshot.observation_date.desc())
                    .limit(1)
                )
                m_snap = (await self.session.execute(m_snap_stmt)).scalar_one_or_none()
                if m_snap:
                    estimated_floor = m_snap.floor_value
                    valuation_source = "MODEL_FLOOR"
                else:
                    pos_warning = f"Model '{p.model.model_name if p.model else p.model_id}' has no recorded model floor; falling back to collection floor."
                    warnings.append(pos_warning)

            # 2. Fallback to collection floor
            if estimated_floor is None and p.collection_id:
                c_snap_stmt = (
                    select(CollectionFloorSnapshot)
                    .where(CollectionFloorSnapshot.collection_id == p.collection_id)
                    .order_by(CollectionFloorSnapshot.observation_date.desc())
                    .limit(1)
                )
                c_snap = (await self.session.execute(c_snap_stmt)).scalar_one_or_none()
                if c_snap:
                    estimated_floor = c_snap.floor_value
                    if p.model_id and valuation_source == "COLLECTION_FLOOR":
                        valuation_source = "COLLECTION_FLOOR_FALLBACK"
                else:
                    pos_warning = f"Collection '{p.collection.collection_name if p.collection else p.collection_id}' has no recorded floor snapshot."
                    warnings.append(pos_warning)

            # Compute values
            if estimated_floor is not None:
                est_val = p.quantity * estimated_floor
                total_estimated += est_val
                pnl = est_val - cost
                pnl_pct = round(((est_val - cost) / cost) * Decimal("100"), 2) if cost > 0 else Decimal("0.0")
                floor_val_float = float(estimated_floor)
                est_val_float = float(est_val)
                pnl_float = float(pnl)
                pnl_pct_float = float(pnl_pct)

                col_name = p.collection.collection_name if p.collection else "Unknown"
                col_distribution[col_name] = col_distribution.get(col_name, Decimal("0.0")) + est_val
            else:
                floor_val_float = 0.0
                est_val_float = 0.0
                pnl_float = float(-cost)
                pnl_pct_float = -100.0

            pos_summaries.append({
                "id": p.id,
                "collection_id": p.collection_id,
                "collection_name": p.collection.collection_name if p.collection else "",
                "collection_slug": p.collection.collection_slug if p.collection else "",
                "model_id": p.model_id,
                "model_name": p.model.model_name if p.model else None,
                "quantity": float(p.quantity),
                "purchase_price": float(p.purchase_price),
                "purchase_date": p.purchase_date,
                "cost_basis": float(cost),
                "estimated_floor": floor_val_float,
                "estimated_value": est_val_float,
                "unrealized_pnl": pnl_float,
                "pnl_pct": pnl_pct_float,
                "valuation_source": valuation_source,
                "warning": pos_warning,
                "notes": p.notes,
            })

        total_pnl = total_estimated - total_cost
        total_pnl_pct = (
            round((total_pnl / total_cost) * Decimal("100"), 2) if total_cost > 0 else Decimal("0.0")
        )

        # Asset distribution percentages
        distribution_chart = []
        if total_estimated > 0:
            for cname, val in col_distribution.items():
                pct = round((val / total_estimated) * Decimal("100"), 1)
                distribution_chart.append({
                    "collection": cname,
                    "value": float(val),
                    "percentage": float(pct),
                })
        distribution_chart.sort(key=lambda x: x["value"], reverse=True)

        return {
            "portfolio_id": portfolio_id,
            "total_estimated_value": float(total_estimated),
            "total_cost_basis": float(total_cost),
            "total_unrealized_pnl": float(total_pnl),
            "total_pnl_pct": float(total_pnl_pct),
            "currency": "GRAM",
            "positions": pos_summaries,
            "distribution": distribution_chart,
            "warnings": warnings,
            "disclaimer": MARKET_DISCLAIMER,
            "attribution": DATA_ATTRIBUTION_TEXT,
            "attribution_url": DATA_ATTRIBUTION_URL,
        }
