import React, { useEffect, useState } from 'react';
import { ArrowLeft, ShieldCheck, RefreshCw } from 'lucide-react';
import { api } from '../../services/api';
import { TGGIIndex } from '../../types';

interface IndexScreenProps {
  onBack: () => void;
  onSelectCollection: (slug: string) => void;
}

export const IndexScreen: React.FC<IndexScreenProps> = ({ onBack, onSelectCollection }) => {
  const [indexData, setIndexData] = useState<TGGIIndex | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadIndex();
  }, []);

  const loadIndex = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getIndex();
      setIndexData(res);
    } catch (e: any) {
      console.error(e);
      setError(e?.message || 'Indeks maʼlumotlarini yuklashda xatolik yuz berdi');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-state">
        <div className="spinner"></div>
        <p>GiftPulse Index maʼlumotlari yuklanmoqda...</p>
      </div>
    );
  }

  if (error || !indexData) {
    return (
      <div className="loading-state">
        <p style={{ color: '#ef4444', marginBottom: 12 }}>{error || 'Indeks maʼlumotlari topilmadi'}</p>
        <button className="primary-action-btn" onClick={loadIndex}>
          <RefreshCw size={16} /> Qayta urinish
        </button>
      </div>
    );
  }

  const isPos = (indexData.change_1d_pct || 0) >= 0;

  return (
    <div className="index-view">
      <button className="back-nav-btn" onClick={onBack}>
        <ArrowLeft size={16} /> Bosh sahifaga qaytish
      </button>

      <div className="index-hero">
        <span className="badge">GiftPulse Benchmark</span>
        <h2>{indexData.name} ({indexData.symbol})</h2>
        <span className="index-date">Kuzatuv sanasi: <code>{indexData.latest_date}</code></span>

        <div className="hero-values">
          <span className="hero-val">{indexData.latest_value.toFixed(2)}</span>
          <span className={`hero-change ${isPos ? 'pos' : 'neg'}`}>
            {isPos ? '+' : ''}{indexData.change_1d_pct.toFixed(2)}% (24s)
          </span>
        </div>

        <div className="hero-meta">
          <span>7 kunlik oʻzgarish: <b>{indexData.change_7d_pct > 0 ? '+' : ''}{indexData.change_7d_pct.toFixed(2)}%</b></span>
          <span>Tarkib: <b>{indexData.constituents_count} ta kolleksiya</b></span>
        </div>
      </div>

      {/* Constituents Table */}
      <div className="constituents-section">
        <h3>Indeks Tarkibidagi Kolleksiyalar</h3>
        <p className="section-sub">Telegram Gifts bozorining eng likvid kolleksiyalari va ularning indeksdagi vazni:</p>

        <div className="constituents-table">
          <div className="c-row header">
            <span>Kolleksiya</span>
            <span>Floor (GRAM)</span>
            <span>24s %</span>
            <span>Vazni (%)</span>
          </div>
          {(indexData.constituents || []).map((c) => {
            const cPos = (c.change_pct || 0) >= 0;
            return (
              <div
                key={c.slug}
                className="c-row click"
                onClick={() => onSelectCollection(c.slug)}
              >
                <span className="c-name">{c.name}</span>
                <span className="c-floor">{c.floor_gram?.toLocaleString()} G</span>
                <span className={`c-change ${cPos ? 'pos' : 'neg'}`}>
                  {c.change_pct !== undefined ? `${cPos ? '+' : ''}${c.change_pct}%` : '-'}
                </span>
                <span className="c-weight">{c.weight_pct}%</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Analytics Notice */}
      <div className="attribution-footer">
        <p>
          📊 <b>GiftPulse Index (GPI):</b> Telegram Collectible Gifts bozorining umumiy harakati va likvidligini kuzatuvchi rasmiy agregat indeks.
        </p>
        <p className="note">
          Har kuni bozor maʼlumotlari asosida yangilanadi.
        </p>
      </div>
    </div>
  );
};
