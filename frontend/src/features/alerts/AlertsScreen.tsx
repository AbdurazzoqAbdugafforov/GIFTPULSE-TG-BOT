import React, { useEffect, useState } from 'react';
import { Bell, Plus, Pause, Play, Trash2, X } from 'lucide-react';
import { api } from '../../services/api';
import { AlertItem, GiftCollection } from '../../types';
import { TelegramWebApp } from '../../telegram/webapp';

interface AlertsScreenProps {
  initialCollectionId?: number;
  initialCollectionName?: string;
  onClearInitial?: () => void;
}

export const AlertsScreen: React.FC<AlertsScreenProps> = ({
  initialCollectionId,
  initialCollectionName,
  onClearInitial,
}) => {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [collections, setCollections] = useState<GiftCollection[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(!!initialCollectionId);

  // Form states
  const [selectedColId, setSelectedColId] = useState<number>(initialCollectionId || 0);
  const [alertType, setAlertType] = useState('COLLECTION_FLOOR_ABOVE');
  const [targetValue, setTargetValue] = useState('');
  const [isRecurring, setIsRecurring] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    loadAlerts();
    loadCollections();
  }, []);

  useEffect(() => {
    if (initialCollectionId) {
      setSelectedColId(initialCollectionId);
      setShowCreateModal(true);
    }
  }, [initialCollectionId]);

  const loadAlerts = async () => {
    try {
      setLoading(true);
      const res = await api.getAlerts();
      setAlerts(res);
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
      if (!selectedColId && res.items.length > 0) {
        setSelectedColId(res.items[0].id);
      }
    } catch (e) {}
  };

  const handleTogglePause = async (alert: AlertItem) => {
    TelegramWebApp.hapticFeedback('selection');
    try {
      if (alert.status === 'ACTIVE') {
        await api.pauseAlert(alert.id);
      } else {
        await api.resumeAlert(alert.id);
      }
      loadAlerts();
    } catch (e) {
      console.error(e);
    }
  };

  const handleDelete = async (alertId: number) => {
    TelegramWebApp.hapticFeedback('warning');
    try {
      await api.deleteAlert(alertId);
      setAlerts((prev) => prev.filter((a) => a.id !== alertId));
    } catch (e) {
      console.error(e);
    }
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    const num = parseFloat(targetValue);
    if (!num || num <= 0) {
      setErrorMsg('Iltimos, toʻgʻri musbat son kiriting.');
      return;
    }

    try {
      setSubmitting(true);
      await api.createAlert({
        collection_id: selectedColId,
        alert_type: alertType,
        target_value: num,
        is_recurring: isRecurring,
      });
      TelegramWebApp.hapticFeedback('success');
      setShowCreateModal(false);
      setTargetValue('');
      if (onClearInitial) onClearInitial();
      loadAlerts();
    } catch (err: any) {
      setErrorMsg(err.message || 'Signal yaratishda xatolik');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="alerts-view">
      <div className="alerts-top-bar">
        <div>
          <h2>Narx Signallari</h2>
          <p>Yangi kunlik snapshot yuklanganda avtomatik xabar beradi</p>
        </div>
        <button
          className="create-btn"
          onClick={() => {
            setShowCreateModal(true);
            setErrorMsg('');
          }}
        >
          <Plus size={16} /> Yangi Signal
        </button>
      </div>

      {loading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Signallar yuklanmoqda...</p>
        </div>
      ) : alerts.length === 0 ? (
        <div className="empty-state">
          <Bell size={36} className="empty-icon" />
          <p>Hozircha faol signallar yoʻq.</p>
          <button className="primary-btn" onClick={() => setShowCreateModal(true)}>
            Signal Oʻrnatish
          </button>
        </div>
      ) : (
        <div className="alerts-list">
          {alerts.map((a) => {
            const isActive = a.status === 'ACTIVE';
            return (
              <div key={a.id} className={`alert-card ${!isActive ? 'paused' : ''}`}>
                <div className="alert-info">
                  <div className="a-title-row">
                    <span className="a-name">{a.collection_name}</span>
                    {a.model_name && <span className="a-model">({a.model_name})</span>}
                    <span className={`status-badge ${a.status.toLowerCase()}`}>
                      {a.status}
                    </span>
                  </div>
                  <div className="a-details-row">
                    <span className="a-type">{a.alert_type.replace('COLLECTION_', '')}</span>
                    <span className="a-target">Maqsad: <b>{a.target_value}</b></span>
                  </div>
                  {a.is_recurring && <span className="recurring-tag">Takroriy (Recurring)</span>}
                </div>

                <div className="alert-actions">
                  <button
                    className="icon-btn"
                    onClick={() => handleTogglePause(a)}
                    title={isActive ? 'Pauza' : 'Davom ettirish'}
                  >
                    {isActive ? <Pause size={16} /> : <Play size={16} />}
                  </button>
                  <button
                    className="icon-btn danger"
                    onClick={() => handleDelete(a.id)}
                    title="Oʻchirish"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create Alert Modal */}
      {showCreateModal && (
        <div className="modal-backdrop">
          <div className="modal-content">
            <div className="modal-header">
              <h3>Yangi Narx Signali</h3>
              <button
                className="close-btn"
                onClick={() => {
                  setShowCreateModal(false);
                  if (onClearInitial) onClearInitial();
                }}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} className="modal-form">
              {errorMsg && <div className="error-alert">{errorMsg}</div>}

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
                <label>Signal Turi</label>
                <select
                  value={alertType}
                  onChange={(e) => setAlertType(e.target.value)}
                >
                  <option value="COLLECTION_FLOOR_ABOVE">Floor darajadan oshganda (Price Above)</option>
                  <option value="COLLECTION_FLOOR_BELOW">Floor darajadan tushganda (Price Below)</option>
                  <option value="COLLECTION_FLOOR_PCT_UP">Floor foizi oshganda (+% Up)</option>
                  <option value="COLLECTION_FLOOR_PCT_DOWN">Floor foizi tushganda (-% Down)</option>
                </select>
              </div>

              <div className="form-group">
                <label>Maqsadli Qiymat (GRAM yoki Foiz)</label>
                <input
                  type="number"
                  step="any"
                  placeholder="Masalan: 250"
                  value={targetValue}
                  onChange={(e) => setTargetValue(e.target.value)}
                  required
                />
              </div>

              <div className="form-checkbox">
                <label>
                  <input
                    type="checkbox"
                    checked={isRecurring}
                    onChange={(e) => setIsRecurring(e.target.checked)}
                  />
                  <span>Takroriy rejim (Recurring cooldown bilan)</span>
                </label>
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="secondary-btn"
                  onClick={() => setShowCreateModal(false)}
                >
                  Bekor qilish
                </button>
                <button
                  type="submit"
                  className="primary-btn"
                  disabled={submitting}
                >
                  {submitting ? 'Saqlanmoqda...' : 'Signalni Saqlash'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
