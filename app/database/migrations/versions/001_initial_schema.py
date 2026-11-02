"""Initial schema migration for GiftPulse

Revision ID: 001_giftpulse
Revises: 
Create Date: 2026-11-02 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_giftpulse'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=64), nullable=True),
        sa.Column('first_name', sa.String(length=128), nullable=True),
        sa.Column('language', sa.String(length=8), nullable=False, server_default='uz'),
        sa.Column('timezone', sa.String(length=64), nullable=False, server_default='Asia/Tashkent'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_telegram_id', 'users', ['telegram_id'], unique=True)

    # 2. user_settings
    op.create_table(
        'user_settings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('notifications_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('daily_report_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('daily_report_time', sa.String(length=8), nullable=False, server_default='09:00'),
        sa.Column('preferred_price_unit', sa.String(length=10), nullable=False, server_default='GRAM'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_user_settings_user_id', 'user_settings', ['user_id'], unique=True)

    # 3. gift_collections
    op.create_table(
        'gift_collections',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('collection_slug', sa.String(length=64), nullable=False),
        sa.Column('collection_name', sa.String(length=128), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_gift_collections_slug', 'gift_collections', ['collection_slug'], unique=True)
    op.create_index('ix_gift_collections_name', 'gift_collections', ['collection_name'])

    # 4. collection_floor_snapshots
    op.create_table(
        'collection_floor_snapshots',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('collection_id', sa.Integer(), nullable=False),
        sa.Column('observation_date', sa.String(length=10), nullable=False),
        sa.Column('floor_value', sa.Numeric(precision=20, scale=4), nullable=False),
        sa.Column('recent_sales', sa.String(length=32), nullable=True),
        sa.Column('source', sa.String(length=128), nullable=False, server_default='Fragment public pages via TG Gifts (tggifts.com)'),
        sa.Column('source_generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('data_confidence', sa.String(length=32), nullable=False, server_default='CONFIRMED'),
        sa.ForeignKeyConstraint(['collection_id'], ['gift_collections.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('collection_id', 'observation_date', name='uq_collection_floor_observation'),
    )
    op.create_index('ix_coll_floor_obs_date', 'collection_floor_snapshots', ['collection_id', 'observation_date'])

    # 5. gift_models
    op.create_table(
        'gift_models',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('collection_id', sa.Integer(), nullable=False),
        sa.Column('model_name', sa.String(length=128), nullable=False),
        sa.Column('model_slug', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['collection_id'], ['gift_collections.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('collection_id', 'model_name', name='uq_model_collection_name'),
    )
    op.create_index('ix_gift_models_collection_id', 'gift_models', ['collection_id'])
    op.create_index('ix_gift_models_name', 'gift_models', ['model_name'])

    # 6. model_floor_snapshots
    op.create_table(
        'model_floor_snapshots',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('model_id', sa.Integer(), nullable=False),
        sa.Column('observation_date', sa.String(length=10), nullable=False),
        sa.Column('floor_value', sa.Numeric(precision=20, scale=4), nullable=False),
        sa.Column('rarity_permille', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('buy_now_listings', sa.Integer(), nullable=True),
        sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['model_id'], ['gift_models.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('model_id', 'observation_date', name='uq_model_floor_observation'),
    )
    op.create_index('ix_model_floor_obs_date', 'model_floor_snapshots', ['model_id', 'observation_date'])

    # 7. market_index_snapshots
    op.create_table(
        'market_index_snapshots',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('observation_date', sa.String(length=10), nullable=False),
        sa.Column('index_value', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('change_pct', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('constituents', sa.Integer(), nullable=True),
        sa.Column('constituents_data', sa.JSON(), nullable=True),
        sa.Column('source', sa.String(length=128), nullable=False, server_default='Public Fragment pages, read by TG Gifts (tggifts.com)'),
        sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('observation_date', name='uq_market_index_observation_date'),
    )
    op.create_index('ix_market_index_date', 'market_index_snapshots', ['observation_date'])

    # 8. watchlist_entries
    op.create_table(
        'watchlist_entries',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('collection_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['collection_id'], ['gift_collections.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'collection_id', name='uq_watchlist_user_collection'),
    )
    op.create_index('ix_watchlist_user_id', 'watchlist_entries', ['user_id'])

    # 9. subscription_plans
    op.create_table(
        'subscription_plans',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('price', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='UZS'),
        sa.Column('duration_days', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('alert_limit', sa.Integer(), nullable=False),
        sa.Column('watchlist_limit', sa.Integer(), nullable=False),
        sa.Column('feature_permissions', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_subscription_plans_code', 'subscription_plans', ['code'], unique=True)

    # 10. subscriptions
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('starts_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['plan_id'], ['subscription_plans.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_subscriptions_user_id', 'subscriptions', ['user_id'])

    # 11. payments
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='UZS'),
        sa.Column('payment_method', sa.String(length=32), nullable=False, server_default='MANUAL_TRANSFER'),
        sa.Column('transaction_reference', sa.String(length=128), nullable=True),
        sa.Column('receipt_file_id', sa.String(length=256), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDING'),
        sa.Column('reviewed_by', sa.BigInteger(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['plan_id'], ['subscription_plans.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_payments_user_id', 'payments', ['user_id'])
    op.create_index('ix_payments_status', 'payments', ['status'])

    # 12. alerts
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('collection_id', sa.Integer(), nullable=False),
        sa.Column('model_id', sa.Integer(), nullable=True),
        sa.Column('alert_type', sa.String(length=48), nullable=False),
        sa.Column('target_value', sa.Numeric(precision=20, scale=4), nullable=False),
        sa.Column('baseline_value', sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('is_recurring', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('cooldown_seconds', sa.Integer(), nullable=False, server_default='86400'),
        sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_evaluated_snapshot', sa.String(length=10), nullable=True),
        sa.Column('trigger_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['collection_id'], ['gift_collections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['model_id'], ['gift_models.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_alerts_user_id', 'alerts', ['user_id'])
    op.create_index('ix_alerts_collection_id', 'alerts', ['collection_id'])
    op.create_index('ix_alerts_status', 'alerts', ['status'])

    # 13. alert_events
    op.create_table(
        'alert_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('alert_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('observed_value', sa.Numeric(precision=20, scale=4), nullable=False),
        sa.Column('target_value', sa.Numeric(precision=20, scale=4), nullable=False),
        sa.Column('observation_date', sa.String(length=10), nullable=False),
        sa.Column('deduplication_key', sa.String(length=128), nullable=False),
        sa.Column('notification_status', sa.String(length=20), nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['alert_id'], ['alerts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('deduplication_key', name='uq_alert_event_dedup_key'),
    )
    op.create_index('ix_alert_events_alert_id', 'alert_events', ['alert_id'])
    op.create_index('ix_alert_events_user_id', 'alert_events', ['user_id'])

    # 14. portfolios
    op.create_table(
        'portfolios',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False, server_default='Main Portfolio'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_portfolios_user_id', 'portfolios', ['user_id'])

    # 15. portfolio_positions
    op.create_table(
        'portfolio_positions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('portfolio_id', sa.Integer(), nullable=False),
        sa.Column('collection_id', sa.Integer(), nullable=False),
        sa.Column('model_id', sa.Integer(), nullable=True),
        sa.Column('quantity', sa.Numeric(precision=18, scale=4), nullable=False, server_default='1.0'),
        sa.Column('purchase_price', sa.Numeric(precision=20, scale=4), nullable=False),
        sa.Column('purchase_date', sa.String(length=10), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['collection_id'], ['gift_collections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['model_id'], ['gift_models.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_portfolio_positions_port_id', 'portfolio_positions', ['portfolio_id'])

    # 16. ingestion_runs
    op.create_table(
        'ingestion_runs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('provider', sa.String(length=64), nullable=False, server_default='TG_GIFTS'),
        sa.Column('dataset_name', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('observation_date', sa.String(length=10), nullable=True),
        sa.Column('records_received', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('records_inserted', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_ingestion_runs_dataset', 'ingestion_runs', ['dataset_name'])

    # 17. audit_logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('actor_telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('action', sa.String(length=64), nullable=False),
        sa.Column('target_type', sa.String(length=64), nullable=False),
        sa.Column('target_id', sa.String(length=64), nullable=False),
        sa.Column('metadata_payload', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_logs_actor', 'audit_logs', ['actor_telegram_id'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('ingestion_runs')
    op.drop_table('portfolio_positions')
    op.drop_table('portfolios')
    op.drop_table('alert_events')
    op.drop_table('alerts')
    op.drop_table('payments')
    op.drop_table('subscriptions')
    op.drop_table('subscription_plans')
    op.drop_table('watchlist_entries')
    op.drop_table('market_index_snapshots')
    op.drop_table('model_floor_snapshots')
    op.drop_table('gift_models')
    op.drop_table('collection_floor_snapshots')
    op.drop_table('gift_collections')
    op.drop_table('user_settings')
    op.drop_table('users')
