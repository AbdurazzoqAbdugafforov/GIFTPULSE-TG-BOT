import React, { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown, Flame, Compass, ExternalLink } from 'lucide-react';
import { api } from '../../services/api';
import { RadarData } from '../../types';

interface RadarScreenProps {
  onSelectCollection: (slug: string) => void;
}

export const RadarScreen: React.FC<RadarScreenProps> = ({ onSelectCollection }) => {
  const [data, setData] = useState<RadarData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRadar();
  }, []);

  const loadRadar = async () => {
    try {
      setLoading(true);
      const res = await api.getRadar();
      setData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !data) {
    return (
      <div className="loading-state">
        <div className="spinner"></div>
        <p>Bozor Radari hisoblanmoqda...</p>
      </div>
    );
  }

  const idx = data.index_summary;
  const isIdxPos = (idx.change_1d_pct || 0) >= 0;

  return (
    <div className="radar-view">
      <div className="radar-banner">
        <Compass size={22} className="radar-icon" />
        <div>
          <h2>Bozor Radari</h2>
          <p>Kunlik snapshotlar boʻyicha eng katta harakatlar va dinamika</p>
        </div>
      </div>

      {/* Index Sentiment */}
      <div className="radar-index-bar">
        <span>GiftPulse Index (GPI): <b>{idx.value?.toFixed(2)}</b></span>
        <span className={`pill ${isIdxPos ? 'pos' : 'neg'}`}>
          {isIdxPos ? '+' : ''}{idx.change_1d_pct?.toFixed(2)}% (24s)
        </span>
      </div>

      {/* 24h Movers Grid */}
      <div className="radar-movers-grid">
        <div className="radar-block">
          <div className="b-header pos">
            <TrendingUp size={16} /> <span>Top Oʻsganlar (24s)</span>
          </div>
          {data.top_gainers_1d.map((g) => (
            <div key={g.slug} className="r-item" onClick={() => onSelectCollection(g.slug)}>
              <span className="col-name">{g.name}</span>
              <div className="col-stats">
                <span className="floor">{g.floor_gram.toLocaleString()} G</span>
                <span className="badge pos">+{g.change_1d_pct}%</span>
              </div>
            </div>
          ))}
        </div>

        <div className="radar-block">
          <div className="b-header neg">
            <TrendingDown size={16} /> <span>Top Tushganlar (24s)</span>
          </div>
          {data.top_losers_1d.map((l) => (
            <div key={l.slug} className="r-item" onClick={() => onSelectCollection(l.slug)}>
              <span className="col-name">{l.name}</span>
              <div className="col-stats">
                <span className="floor">{l.floor_gram.toLocaleString()} G</span>
                <span className="badge neg">{l.change_1d_pct}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 7d Movers Grid */}
      <div className="radar-movers-grid">
        <div className="radar-block">
          <div className="b-header pos">
            <TrendingUp size={16} /> <span>Haftalik Top Oʻsish (7 kun)</span>
          </div>
          {data.top_gainers_7d.map((g) => (
            <div key={g.slug} className="r-item" onClick={() => onSelectCollection(g.slug)}>
              <span className="col-name">{g.name}</span>
              <div className="col-stats">
                <span className="floor">{g.floor_gram.toLocaleString()} G</span>
                <span className="badge pos">+{g.change_7d_pct}%</span>
              </div>
            </div>
          ))}
        </div>

        <div className="radar-block">
          <div className="b-header active-sales">
            <Flame size={16} /> <span>Faol Savdolar</span>
          </div>
          {data.active_sales_collections.map((s) => (
            <div key={s.slug} className="r-item" onClick={() => onSelectCollection(s.slug)}>
              <span className="col-name">{s.name}</span>
              <div className="col-stats">
                <span className="sales-cnt">{s.recent_sales} sotuv</span>
                <span className="floor">{s.floor_gram.toLocaleString()} G</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Disclaimer */}
      <div className="radar-disclaimer">
        <p>⚠️ <b>Ogohlantirish:</b> Ushbu koʻrsatkichlar tahliliy hisob-kitoblar boʻlib, moliyaviy yoki investitsiya maslahati hisoblanmaydi.</p>
        <p>
          📊 <b>GiftPulse Market Intelligence</b>
        </p>
      </div>
    </div>
  );
};
