import React from 'react';
import { Maximize2, Sparkles } from 'lucide-react';
import { TelegramWebApp } from '../telegram/webapp';

interface HeaderProps {
  indexValue?: number;
  indexChange?: number;
  dataFreshness?: string;
}

export const Header: React.FC<HeaderProps> = ({ indexValue, indexChange, dataFreshness }) => {
  const handleExpand = () => {
    TelegramWebApp.expand();
  };

  const isPositive = (indexChange || 0) >= 0;

  return (
    <header className="header-container">
      <div className="header-top">
        <div className="header-brand">
          <div className="brand-logo">🎁</div>
          <div>
            <h1 className="brand-title">GiftPulse</h1>
            <p className="brand-subtitle">Telegram Gifts Analytics</p>
          </div>
        </div>

        <div className="header-actions">
          {indexValue !== undefined && (
            <div className={`index-badge ${isPositive ? 'positive' : 'negative'}`}>
              <span className="index-name">GPI</span>
              <span className="index-val">{indexValue.toFixed(2)}</span>
              <span className="index-change">
                {isPositive ? '+' : ''}
                {(indexChange || 0).toFixed(2)}%
              </span>
            </div>
          )}

          <button
            onClick={handleExpand}
            className="expand-btn"
            title="Kengaytirish (Expand)"
            aria-label="Expand App"
          >
            <Maximize2 size={16} />
          </button>
        </div>
      </div>

      <div className="attribution-bar">
        <span className="platform-tag" style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: 'var(--text-secondary)' }}>
          <Sparkles size={12} color="#38bdf8" /> Telegram Collectible Gifts Analytics
        </span>
        <span className="freshness-tag">
          {dataFreshness === 'STALE' ? '⚠️ Yangilanmoqda' : '● Jonli Bozor'}
        </span>
      </div>
    </header>
  );
};
