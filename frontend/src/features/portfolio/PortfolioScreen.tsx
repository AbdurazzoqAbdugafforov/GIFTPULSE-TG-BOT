import React, { useEffect, useState } from 'react';
import { Briefcase, Plus, Trash2, AlertTriangle, X } from 'lucide-react';
import { api } from '../../services/api';
import { GiftCollection, PortfolioSummary } from '../../types';
import { TelegramWebApp } from '../../telegram/webapp';

export const PortfolioScreen: React.FC = () => {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [collections, setCollections] = useState<GiftCollection[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);

  // Form states
  const [selectedColId, setSelectedColId] = useState<number>(0);
  const [quantity, setQuantity] = useState('1');
  const [purchasePrice, setPurchasePrice] = useState('');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadPortfolio();
    loadCollections();
  }, []);

  const loadPortfolio = async () => {
    try {
      setLoading(true);
      const res = await api.getPortfolio();
      setSummary(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const loadCollections = async () => {
    try {
      const res = await api.getCollections(undefined, 'name_asc', 200);
      setCollections(res.items);
      if (res.items.length > 0) {
        setSelectedColId(res.items[0].id);
      }
    } catch (e) {}
  };

  const handleDeletePosition = async (posId: number) => {
    TelegramWebApp.hapticFeedback('warning');
    try {
      await api.deletePortfolioPosition(posId);
      loadPortfolio();
    } catch (e) {
      console.error(e);
    }
  };

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const qty = parseFloat(quantity);
    const price = parseFloat(purchasePrice);
    if (!qty || qty <= 0 || !price || price <= 0) return;

    try {
      setSubmitting(true);
      await api.addPortfolioPosition({
        collection_id: selectedColId,
        quantity: qty,
        purchase_price: price,
        notes: notes || undefined,
      });
      TelegramWebApp.hapticFeedback('success');
      setShowAddModal(false);
      setQuantity('1');
      setPurchasePrice('');
      setNotes('');
      loadPortfolio();
    } catch (e) {
      console.error(e);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading || !summary) {
    return (
      <div className="loading-state">
        <div className="spinner"></div>
        <p>Portfel maʼlumotlari hisoblanmoqda...</p>
      </div>
    );
  }

  const isProfit = summary.total_unrealized_pnl >= 0;

  return (
    <div className="portfolio-view">
      {/* Portfolio Total Card */}
      <div className="portfolio-card">
        <div className="p-header">
          <div>
            <span className="p-tag">Taxminiy Qiymat</span>
            <h2 className="p-total">{summary.total_estimated_value.toLocaleString()} GRAM</h2>
          </div>
          <button className="add-pos-btn" onClick={() => setShowAddModal(true)}>
            <Plus size={16} /> Qoʻshish
          </button>
        </div>

        <div className="p-metrics">
          <div className="m-item">
            <span className="m-label">Xarid Xarajati</span>
            <span className="m-val">{summary.total_cost_basis.toLocaleString()} GRAM</span>
          </div>
          <div className="m-item">
            <span className="m-label">Kutilayotgan PnL</span>
            <span className={`m-val ${isProfit ? 'pos' : 'neg'}`}>
              {isProfit ? '+' : ''}{summary.total_unrealized_pnl.toLocaleString()} GRAM ({isProfit ? '+' : ''}{summary.total_pnl_pct.toFixed(2)}%)
            </span>
          </div>
        </div>
      </div>

      {/* Warnings Banner if any */}
      {summary.warnings && summary.warnings.length > 0 && (
        <div className="warnings-banner">
          <div className="w-header">
            <AlertTriangle size={16} /> <span>Baholash Eslatmasi:</span>
          </div>
          <ul>
            {summary.warnings.slice(0, 3).map((w, idx) => (
              <li key={idx}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Asset Distribution */}
      {summary.distribution && summary.distribution.length > 0 && (
        <div className="distribution-section">
          <h3>Kolleksiyalar Boʻyicha Taqsimot</h3>
          <div className="dist-bar">
            {summary.distribution.map((d, i) => (
              <div
                key={i}
                className="dist-segment"
                style={{ width: `${Math.max(d.percentage, 5)}%`, opacity: 1 - i * 0.15 }}
                title={`${d.collection}: ${d.percentage}%`}
              />
            ))}
          </div>
          <div className="dist-legend">
            {summary.distribution.slice(0, 4).map((d, i) => (
              <span key={i} className="dist-legend-item">
                <b>{d.collection}</b> ({d.percentage}%)
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Holdings List */}
      <div className="holdings-section">
        <h3>Mavjud Sovgʻalar ({summary.positions.length} ta)</h3>

        {summary.positions.length === 0 ? (
          <div className="empty-state">
            <Briefcase size={36} className="empty-icon" />
            <p>Hozircha portfelda aktivlar yoʻq.</p>
            <button className="primary-btn" onClick={() => setShowAddModal(true)}>
              Gift Qoʻshish
            </button>
          </div>
        ) : (
          <div className="positions-list">
            {summary.positions.map((pos) => {
              const posProfit = pos.unrealized_pnl >= 0;
              return (
                <div key={pos.id} className="position-item">
                  <div className="pos-left">
                    <span className="pos-col">{pos.collection_name}</span>
                    {pos.model_name && <span className="pos-mod">Model: {pos.model_name}</span>}
                    <span className="pos-qty">{pos.quantity} dona • Xarid: {pos.purchase_price} G</span>
                    <span className="pos-source">Baholash: {pos.valuation_source}</span>
                  </div>

                  <div className="pos-right">
                    <span className="pos-val">{pos.estimated_value.toLocaleString()} GRAM</span>
                    <span className={`pos-pnl ${posProfit ? 'pos' : 'neg'}`}>
                      {posProfit ? '+' : ''}{pos.unrealized_pnl.toFixed(1)} G ({posProfit ? '+' : ''}{pos.pnl_pct}%)
                    </span>
                    <button className="pos-del-btn" onClick={() => handleDeletePosition(pos.id)}>
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="portfolio-disclaimer">
        ⚠️ <i>{summary.disclaimer}</i>
      </div>

      {/* Add Position Modal */}
      {showAddModal && (
        <div className="modal-backdrop">
          <div className="modal-content">
            <div className="modal-header">
              <h3>Portfelga Gift Qoʻshish</h3>
              <button className="close-btn" onClick={() => setShowAddModal(false)}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleAddSubmit} className="modal-form">
              <div className="form-group">
                <label>Kolleksiya</label>
                <select
                  value={selectedColId}
                  onChange={(e) => setSelectedColId(Number(e.target.value))}
                >
                  {collections.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} (Floor: {c.floor_gram.toLocaleString()} G)
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Soni (Quantity)</label>
                <input
                  type="number"
                  step="any"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label>Xarid Narxi (Bir dona uchun GRAM)</label>
                <input
                  type="number"
                  step="any"
                  placeholder="Masalan: 120"
                  value={purchasePrice}
                  onChange={(e) => setPurchasePrice(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label>Izoh / Eslatma (ixtiyoriy)</label>
                <input
                  type="text"
                  placeholder="Masalan: Fragmentdan olindi"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                />
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="secondary-btn"
                  onClick={() => setShowAddModal(false)}
                >
                  Bekor qilish
                </button>
                <button
                  type="submit"
                  className="primary-btn"
                  disabled={submitting}
                >
                  {submitting ? 'Qoʻshilmoqda...' : 'Portfelga Saqlash'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
