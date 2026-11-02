export type TabType =
  | 'dashboard'
  | 'markets'
  | 'models'
  | 'alerts'
  | 'portfolio'
  | 'radar'
  | 'index'
  | 'settings'
  | 'subscriptions';

export interface UserProfile {
  id: number;
  telegram_id: number;
  first_name: string;
  username?: string;
  language: string;
  timezone: string;
}

export interface UserPlan {
  code: string;
  name: string;
  alert_limit: number;
  watchlist_limit: number;
  expires_at?: string | null;
}

export interface GiftCollection {
  id: number;
  slug: string;
  name: string;
  floor_gram: number;
  price_unit: string;
  observation_date: string;
  recent_sales?: string | null;
  change_1d_pct: number;
  change_7d_pct: number;
  is_in_watchlist?: boolean;
  history?: Array<{ date: string; floor_gram: number; recent_sales?: string }>;
}

export interface GiftModel {
  id: number;
  collection_id: number;
  collection_slug: string;
  collection_name: string;
  name: string;
  slug?: string | null;
  floor_gram: number;
  price_unit: string;
  rarity_permille?: number | null;
  rarity_pct?: number | null;
  buy_now_listings?: number | null;
  observation_date: string;
  change_1d_pct: number;
  history?: Array<{ date: string; floor_gram: number; buy_now_listings?: number }>;
}

export interface ChartPoint {
  date: string;
  value: number;
  label?: string;
}

export interface TGGIIndex {
  name: string;
  symbol: string;
  latest_value: number;
  change_1d_pct: number;
  change_7d_pct: number;
  latest_date: string;
  constituents_count: number;
  series?: Array<{ date: string; value: number; change_pct?: number }>;
  constituents?: Array<{
    slug: string;
    name: string;
    floor_gram: number;
    weight_pct: number;
    change_pct?: number;
    recent_sales?: string;
  }>;
}

export interface AlertItem {
  id: number;
  collection_id: number;
  collection_name: string;
  collection_slug: string;
  model_id?: number | null;
  model_name?: string | null;
  alert_type: string;
  target_value: number;
  baseline_value?: number | null;
  status: 'ACTIVE' | 'TRIGGERED' | 'PAUSED' | 'DELETED';
  is_recurring: boolean;
  trigger_count: number;
  created_at: string;
}

export interface PortfolioPositionItem {
  id: number;
  collection_id: number;
  collection_name: string;
  collection_slug: string;
  model_id?: number | null;
  model_name?: string | null;
  quantity: number;
  purchase_price: number;
  purchase_date?: string | null;
  cost_basis: number;
  estimated_floor: number;
  estimated_value: number;
  unrealized_pnl: number;
  pnl_pct: number;
  valuation_source: string;
  warning?: string | null;
  notes?: string | null;
}

export interface PortfolioSummary {
  portfolio_id: number;
  total_estimated_value: number;
  total_cost_basis: number;
  total_unrealized_pnl: number;
  total_pnl_pct: number;
  currency: string;
  positions: PortfolioPositionItem[];
  distribution: Array<{ collection: string; value: number; percentage: number }>;
  warnings: string[];
  disclaimer: string;
  attribution: string;
  attribution_url: string;
}

export interface RadarData {
  top_gainers_1d: GiftCollection[];
  top_losers_1d: GiftCollection[];
  top_gainers_7d: GiftCollection[];
  top_losers_7d: GiftCollection[];
  active_sales_collections: GiftCollection[];
  index_summary: {
    value: number;
    change_1d_pct: number;
    change_7d_pct: number;
    date: string;
  };
  disclaimer: string;
  attribution: string;
  attribution_url: string;
}

export interface DashboardData {
  index: {
    name: string;
    symbol: string;
    value: number;
    change_1d_pct: number;
    change_7d_pct: number;
    observation_date: string;
  };
  popular_collections: GiftCollection[];
  top_gainers_1d: GiftCollection[];
  top_losers_1d: GiftCollection[];
  active_alerts_count: number;
  watchlist_count: number;
  data_freshness: string;
  latest_observation_date: string;
  attribution: string;
  attribution_url: string;
}
