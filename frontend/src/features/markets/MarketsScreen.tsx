import React, { useEffect, useState } from 'react';
import { Search, Star, Bell, ArrowLeft, Layers, ExternalLink } from 'lucide-react';
import { api } from '../../services/api';
import { GiftCollection, GiftModel } from '../../types';
import { TelegramWebApp } from '../../telegram/webapp';

interface MarketsScreenProps {
  selectedSlug?: string | null;
  onClearSlug?: () => void;
  onCreateAlert?: (colId: number, colName: string) => void;
}

export const MarketsScreen: React.FC<MarketsScreenProps> = ({
  selectedSlug,
  onClearSlug,
  onCreateAlert,
}) => {
  const [collections, setCollections] = useState<GiftCollection[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('floor_desc');
  const [activeCollection, setActiveCollection] = useState<GiftCollection | null>(null);
  const [collectionModels, setCollectionModels] = useState<GiftModel[]>([]);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [viewingModels, setViewingModels] = useState(false);
  const [watchlistIds, setWatchlistIds] = useState<Set<number>>(new Set());

  useEffect(() => {
    loadCollections();
    loadWatchlist();
  }, [search, sortBy]);

  useEffect(() => {
    if (selectedSlug) {
      loadCollectionDetail(selectedSlug);
    }
  }, [selectedSlug]);

  const loadCollections = async () => {
    try {
      setLoading(true);
      const res = await api.getCollections(search, sortBy, 100);
      setCollections(res.items);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const loadWatchlist = async () => {
    try {
      const items = await api.getWatchlist();
      setWatchlistIds(new Set(items.map((x) => x.id)));
    } catch (e) {}
  };

  const loadCollectionDetail = async (slug: string) => {
    try {
      setLoading(true);
      const col = await api.getCollection(slug);
      setActiveCollection(col);
      setViewingModels(false);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const loadModels = async (slug: string) => {
    try {
      setModelsLoading(true);
      const res = await api.getCollectionModels(slug, undefined, 'floor_desc');
      setCollectionModels(res.items);
      setViewingModels(true);
    } catch (e) {
      console.error(e);
    } finally {
      setModelsLoading(false);
    }
  };

  const handleWatchlistToggle = async (col: GiftCollection) => {
    TelegramWebApp.hapticFeedback('selection');
    const isIn = watchlistIds.has(col.id);
    if (isIn) {
      await api.removeFromWatchlist(col.id);
      setWatchlistIds((prev) => {
        const next = new Set(prev);
        next.delete(col.id);
        return next;
      });
    } else {
      await api.addToWatchlist(col.id);
      setWatchlistIds((prev) => new Set(prev).add(col.id));
    }
  };

  // Detailed Collection View
  if (activeCollection) {
    const isInWatchlist = watchlistIds.has(activeCollection.id);
    const history = activeCollection.history || [];

    return (
      <div className="collection-detail-view">
        <button
          className="back-nav-btn"
          onClick={() => {
            setActiveCollection(null);
            setViewingModels(false);
            if (onClearSlug) onClearSlug();
          }}
        >
          <ArrowLeft size={16} /> Kolleksiyalar roʻyxatiga
        </button>

        <div className="col-detail-header">
          <div>
            <h2 className="title">{activeCollection.name}</h2>
            <span className="slug-tag">slug: {activeCollection.slug}</span>
          </div>
          <button
            className={`wl-btn ${isInWatchlist ? 'active' : ''}`}
            onClick={() => handleWatchlistToggle(activeCollection)}
          >
            <Star size={18} fill={isInWatchlist ? 'currentColor' : 'none'} />
          </button>
        </div>

        <div className="stats-cards-grid">
          <div className="metric-card">
            <span className="label">Floor Narxi</span>
            <span className="val">{activeCollection.floor_gram.toLocaleString()} GRAM</span>
          </div>
          <div className="metric-card">
            <span className="label">24s Oʻzgarish</span>
            <span className={`val ${activeCollection.change_1d_pct >= 0 ? 'pos' : 'neg'}`}>
              {activeCollection.change_1d_pct > 0 ? '+' : ''}
              {activeCollection.change_1d_pct}%
            </span>
          </div>
          <div className="metric-card">
            <span className="label">7 kunlik</span>
            <span className={`val ${activeCollection.change_7d_pct >= 0 ? 'pos' : 'neg'}`}>
              {activeCollection.change_7d_pct > 0 ? '+' : ''}
              {activeCollection.change_7d_pct}%
            </span>
          </div>
          <div className="metric-card">
            <span className="label">Soʻnggi savdolar</span>
            <span className="val">{activeCollection.recent_sales || 'Mavjud emas'}</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="detail-actions-row">
          <button
            className="action-btn secondary"
            onClick={() => loadModels(activeCollection.slug)}
          >
            <Layers size={16} /> Modellar & Noyoblik ({collectionModels.length || 'Koʻrish'})
          </button>

          {onCreateAlert && (
            <button
              className="action-btn primary"
              onClick={() => onCreateAlert(activeCollection.id, activeCollection.name)}
            >
              <Bell size={16} /> Signal Oʻrnatish
            </button>
          )}
        </div>

        {/* Models list if toggled */}
        {viewingModels && (
          <div className="models-section">
            <h3>✨ Kolleksiya Modellari</h3>
            {modelsLoading ? (
              <p>Modellar yuklanmoqda...</p>
            ) : collectionModels.length === 0 ? (
              <p className="empty-note">Ushbu kolleksiya uchun modellar maʼlumoti hozircha mavjud emas.</p>
            ) : (
              <div className="models-list">
                {collectionModels.map((m) => (
                  <div key={m.id} className="model-row">
                    <div className="m-left">
                      <span className="m-name">{m.name}</span>
                      <span className="m-rarity">
                        {m.rarity_pct !== null ? `Noyoblik: ${m.rarity_pct}%` : 'Rarity: N/A'}
                      </span>
                    </div>
                    <div className="m-right">
                      <span className="m-floor">{m.floor_gram.toLocaleString()} GRAM</span>
                      <span className="m-listings">{m.buy_now_listings ? `${m.buy_now_listings} ta sotuvda` : ''}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Historical Floor Chart Preview */}
        {history.length > 0 && (
          <div className="history-table-section">
            <h3>Tarixiy Kunlik Floor Qaydlari</h3>
            <div className="history-table">
              <div className="h-row header">
                <span>Sana</span>
                <span>Floor (GRAM)</span>
                <span>Savdolar</span>
              </div>
              {history.slice(-10).reverse().map((h, i) => (
                <div key={i} className="h-row">
                  <span>{h.date}</span>
                  <span><b>{h.floor_gram.toLocaleString()}</b></span>
                  <span>{h.recent_sales || '-'}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="attribution-footer">
          <p>📊 <b>GiftPulse Market Intelligence</b></p>
          <p className="note">Kunlik tahliliy koʻrsatkichlar. Real vaqt listing hodisasi emas.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="markets-view">
      {/* Search & Sort Bar */}
      <div className="search-sort-bar">
        <div className="search-input-wrap">
          <Search size={16} className="search-icon" />
          <input
            type="text"
            placeholder="Kolleksiya qidirish..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="sort-pills">
          <button
            className={`pill ${sortBy === 'floor_desc' ? 'active' : ''}`}
            onClick={() => setSortBy('floor_desc')}
          >
            Floor ↓
          </button>
          <button
            className={`pill ${sortBy === 'change_1d_desc' ? 'active' : ''}`}
            onClick={() => setSortBy('change_1d_desc')}
          >
            24s %
          </button>
          <button
            className={`pill ${sortBy === 'name_asc' ? 'active' : ''}`}
            onClick={() => setSortBy('name_asc')}
          >
            A-Z
          </button>
        </div>
      </div>

      {/* Collections List */}
      {loading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Kolleksiyalar yuklanmoqda...</p>
        </div>
      ) : collections.length === 0 ? (
        <div className="empty-state">
          <p>Kolleksiya topilmadi.</p>
        </div>
      ) : (
        <div className="collections-list">
          {collections.map((col) => {
            const isPos = col.change_1d_pct >= 0;
            const isInWl = watchlistIds.has(col.id);

            return (
              <div
                key={col.slug}
                className="col-list-item"
                onClick={() => loadCollectionDetail(col.slug)}
              >
                <div className="item-main">
                  <div className="item-title-row">
                    <span className="item-name">{col.name}</span>
                    <button
                      className={`item-wl-star ${isInWl ? 'active' : ''}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleWatchlistToggle(col);
                      }}
                    >
                      <Star size={14} fill={isInWl ? 'currentColor' : 'none'} />
                    </button>
                  </div>
                  <span className="item-slug">@{col.slug}</span>
                </div>

                <div className="item-values">
                  <span className="item-floor">{col.floor_gram.toLocaleString()} GRAM</span>
                  <span className={`item-pct ${isPos ? 'pos' : 'neg'}`}>
                    {isPos ? '+' : ''}{col.change_1d_pct.toFixed(1)}%
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <div className="data-source-tag">
        📊 GiftPulse Market Intelligence
      </div>
    </div>
  );
};
