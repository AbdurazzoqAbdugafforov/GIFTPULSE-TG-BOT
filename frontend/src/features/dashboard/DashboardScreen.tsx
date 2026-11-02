import React, { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown, ArrowRight, Shield, Bell, Star, RefreshCw } from 'lucide-react';
import { api } from '../../services/api';
import { DashboardData, GiftCollection, TabType } from '../../types';

interface DashboardScreenProps {
  onNavigate: (tab: TabType, extra?: any) => void;
  onSelectCollection: (slug: string) => void;
}

export const DashboardScreen: React.FC<DashboardScreenProps> = ({ onNavigate, onSelectCollection }) => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getDashboard();
      setData(res);
    } catch (e: any) {
      console.error('Failed to load dashboard:', e);
      setError(e?.message || 'Maʼlumotlarni yuklashda xatolik yuz berdi');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-state">
        <div className="spinner"></div>
        <p>Bozor maʼlumotlari yuklanmoqda...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="loading-state">
        <p style={{ color: '#ef4444', marginBottom: 12 }}>{error || 'Maʼlumot topilmadi'}</p>
        <button className="primary-action-btn" onClick={loadDashboard}>
          <RefreshCw size={16} /> Qayta urinish
        </button>
      </div>
    );
  }

  const isIndexPos = data.index.change_1d_pct >= 0;

  return (
    <div className="dashboard-view">
      {/* Index Hero Card */}
      <div className="index-card">
        <div className="index-header">
          <div>
            <span className="badge-tag">GiftPulse Benchmark</span>
            <h2 className="index-title">{data.index.name} ({data.index.symbol})</h2>
            <p className="index-date">Kuzatuv sanasi: {data.index.observation_date}</p>
          </div>
          <div className="index-value-block">
            <span className="big-value">{data.index.value.toFixed(2)}</span>
            <span className={`pill-change ${isIndexPos ? 'pos' : 'neg'}`}>
              {isIndexPos ? '+' : ''}{data.index.change_1d_pct.toFixed(2)}% (24s)
            </span>
          </div>
        </div>
        <div className="index-footer">
          <span>7 kunlik dinamika: <b>{data.index.change_7d_pct > 0 ? '+' : ''}{data.index.change_7d_pct.toFixed(2)}%</b></span>
          <button className="text-btn" onClick={() => onNavigate('index')}>
            Tahlil va Tarkib <ArrowRight size={14} />
          </button>
        </div>
      </div>

      {/* Quick Summary Badges */}
      <div className="quick-stats-row">
        <div className="stat-pill" onClick={() => onNavigate('alerts')}>
          <Bell size={18} className="pill-icon" />
          <div>
            <span className="stat-label">Faol signallar</span>
            <span className="stat-num">{data.active_alerts_count} ta</span>
          </div>
        </div>

        <div className="stat-pill" onClick={() => onNavigate('markets')}>
          <Star size={18} className="pill-icon" />
          <div>
            <span className="stat-label">Kuzatuv roʻyxati</span>
            <span className="stat-num">{data.watchlist_count} ta</span>
          </div>
        </div>
      </div>

      {/* Popular Collections */}
      <div className="section-block">
        <div className="section-header">
          <h3>Ommabop Kolleksiyalar</h3>
          <button className="link-btn" onClick={() => onNavigate('markets')}>
            Barchasi <ArrowRight size={14} />
          </button>
        </div>

        <div className="collections-grid">
          {data.popular_collections.map((col) => {
            const isPos = col.change_1d_pct >= 0;
            return (
              <div
                key={col.slug}
                className="collection-card"
                onClick={() => onSelectCollection(col.slug)}
              >
                <div className="col-top">
                  <span className="col-name">{col.name}</span>
                  <span className={`col-change ${isPos ? 'pos' : 'neg'}`}>
                    {isPos ? '+' : ''}{col.change_1d_pct.toFixed(1)}%
                  </span>
                </div>
                <div className="col-bottom">
                  <span className="col-floor">{col.floor_gram.toLocaleString()} GRAM</span>
                  <span className="col-sales">{col.recent_sales ? `${col.recent_sales} sotuv` : ''}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Top Gainers & Losers */}
      <div className="movers-row">
        <div className="mover-col">
          <div className="mover-header pos">
            <TrendingUp size={16} /> <span>Top Oʻsganlar (24s)</span>
          </div>
          {data.top_gainers_1d.map((g) => (
            <div key={g.slug} className="mover-item" onClick={() => onSelectCollection(g.slug)}>
              <span className="name">{g.name}</span>
              <span className="change pos">+{g.change_1d_pct}%</span>
            </div>
          ))}
        </div>

        <div className="mover-col">
          <div className="mover-header neg">
            <TrendingDown size={16} /> <span>Top Tushganlar (24s)</span>
          </div>
          {data.top_losers_1d.map((l) => (
            <div key={l.slug} className="mover-item" onClick={() => onSelectCollection(l.slug)}>
              <span className="name">{l.name}</span>
              <span className="change neg">{l.change_1d_pct}%</span>
            </div>
          ))}
        </div>
      </div>

      {/* Analytics Notice */}
      <div className="attribution-card">
        <p>
          📊 <b>GiftPulse Market Intelligence:</b> Kunlik yangilanuvchi bozor tahlillari va professional koʻrsatkichlar.
        </p>
        <p className="disclaimer-note">
          ⚠️ GiftPulse axborot-tahliliy vositadir. Narxlar kafolatlangan savdo narxi hisoblanmaydi.
        </p>
      </div>
    </div>
  );
};
