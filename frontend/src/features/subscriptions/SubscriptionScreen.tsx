import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { TelegramWebApp } from '../../telegram/webapp';
import { ShieldCheck, Zap, Crown, CheckCircle2, Copy, Send } from 'lucide-react';

export const SubscriptionScreen: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [reference, setReference] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [copied, setCopied] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchSubscription = async () => {
    try {
      setLoading(true);
      const res = await api.getSubscription();
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Obuna maʼlumotlarini yuklashda xatolik');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSubscription();
  }, []);

  const handleCopyCard = (cardNumber: string) => {
    navigator.clipboard.writeText(cardNumber.replace(/\s+/g, ''));
    setCopied(true);
    TelegramWebApp.haptic('selection');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSubmitPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPlan || !reference.trim()) return;

    try {
      setSubmitting(true);
      setError(null);
      await api.submitPayment(selectedPlan, reference.trim());
      TelegramWebApp.haptic('success');
      setSuccessMessage('Toʻlov cheki qabul qilindi! Administrator tasdiqlagach tarifingiz faollashadi.');
      setSelectedPlan(null);
      setReference('');
      fetchSubscription();
    } catch (err: any) {
      setError(err.message || 'Toʻlovni yuborishda xatolik yuz berdi');
      TelegramWebApp.haptic('error');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="empty-state">
        <div className="spinner" />
        <p>Obuna rejalari yuklanmoqda...</p>
      </div>
    );
  }

  const currentPlan = data?.current_plan;
  const availablePlans = data?.available_plans || [];
  const instructions = data?.payment_instructions || {};

  return (
    <div style={{ paddingBottom: '32px' }}>
      <div style={{ marginBottom: '16px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: 700, margin: '0 0 4px 0' }}>Tariflar & Obuna</h2>
        <p style={{ margin: 0, fontSize: '13px', color: 'var(--cp-text-muted)' }}>
          Koʻproq ogohlantirishlar va professional monitoring imkoniyatlari
        </p>
      </div>

      {successMessage && (
        <div
          style={{
            background: 'rgba(34, 197, 94, 0.15)',
            border: '1px solid rgba(34, 197, 94, 0.3)',
            borderRadius: '12px',
            padding: '12px 14px',
            fontSize: '13px',
            color: 'var(--cp-success)',
            marginBottom: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <CheckCircle2 size={16} />
          <span>{successMessage}</span>
        </div>
      )}

      {error && (
        <div
          style={{
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '12px',
            padding: '12px 14px',
            fontSize: '13px',
            color: 'var(--cp-danger)',
            marginBottom: '16px',
          }}
        >
          {error}
        </div>
      )}

      {/* Current plan badge */}
      <div className="card" style={{ marginBottom: '20px', background: 'linear-gradient(135deg, #1c2438 0%, #151b28 100%)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--cp-text-muted)' }}>
              Sizning joriy tarifingiz
            </div>
            <div style={{ fontSize: '22px', fontWeight: 800, color: 'var(--cp-brand)', marginTop: '2px' }}>
              {currentPlan?.name || 'FREE'}
            </div>
          </div>
          <span className="badge badge-brand" style={{ fontSize: '12px', padding: '4px 10px' }}>
            {currentPlan?.code}
          </span>
        </div>

        <div style={{ marginTop: '14px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '12px' }}>
          <div style={{ background: 'var(--cp-bg-surface-elevated)', padding: '8px 10px', borderRadius: '8px' }}>
            <span style={{ color: 'var(--cp-text-muted)' }}>Alert limiti: </span>
            <strong>{currentPlan?.alert_limit} ta</strong>
          </div>
          <div style={{ background: 'var(--cp-bg-surface-elevated)', padding: '8px 10px', borderRadius: '8px' }}>
            <span style={{ color: 'var(--cp-text-muted)' }}>Watchlist: </span>
            <strong>{currentPlan?.watchlist_limit} ta</strong>
          </div>
        </div>

        {currentPlan?.expires_at && (
          <div style={{ marginTop: '10px', fontSize: '11px', color: 'var(--cp-text-muted)' }}>
            Amal qilish muddati: {new Date(currentPlan.expires_at).toLocaleDateString()}
          </div>
        )}
      </div>

      {/* Available Plans */}
      <div style={{ display: 'grid', gap: '14px' }}>
        {availablePlans.map((plan: any) => {
          const isCurrent = currentPlan?.code === plan.code;
          const isPro = plan.code === 'PRO';
          const isElite = plan.code === 'ELITE';

          return (
            <div
              key={plan.code}
              className="card"
              style={{
                border: isCurrent
                  ? '1px solid var(--cp-brand)'
                  : isElite
                  ? '1px solid rgba(234, 179, 8, 0.4)'
                  : '1px solid var(--cp-border)',
                position: 'relative',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    {isElite ? <Crown size={18} color="#eab308" /> : isPro ? <Zap size={18} color="var(--cp-brand)" /> : <ShieldCheck size={18} color="var(--cp-text-muted)" />}
                    <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700 }}>{plan.name}</h3>
                  </div>
                  <div style={{ fontSize: '20px', fontWeight: 800, marginTop: '4px' }}>
                    {Number(plan.price) === 0 ? 'Bepul' : `${Number(plan.price).toLocaleString()} ${plan.currency}`}
                    {Number(plan.price) > 0 && <span style={{ fontSize: '12px', fontWeight: 400, color: 'var(--cp-text-muted)' }}> / {plan.duration_days} kun</span>}
                  </div>
                </div>

                {isCurrent ? (
                  <span className="badge badge-success">Faol</span>
                ) : (
                  <button
                    className="btn btn-secondary"
                    style={{ padding: '6px 14px', fontSize: '12px' }}
                    onClick={() => {
                      setSelectedPlan(plan.code);
                      TelegramWebApp.haptic('selection');
                    }}
                  >
                    Tanlash
                  </button>
                )}
              </div>

              <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--cp-text)' }}>
                  <CheckCircle2 size={13} color="var(--cp-success)" />
                  <span>Maksimal <strong>{plan.alert_limit} ta</strong> narx signali</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--cp-text)' }}>
                  <CheckCircle2 size={13} color="var(--cp-success)" />
                  <span>Kuzatuv roʻyxati: <strong>{plan.watchlist_limit} ta</strong> kriptovalyuta</span>
                </div>
                {plan.features?.market_radar && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--cp-text)' }}>
                    <CheckCircle2 size={13} color="var(--cp-success)" />
                    <span>Bozor Radari (Top geynerlar & anomaliyalar)</span>
                  </div>
                )}
                {plan.features?.recurring_alerts && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--cp-text)' }}>
                    <CheckCircle2 size={13} color="var(--cp-success)" />
                    <span>Takroriy avtomatik signallar</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Payment Sheet / Modal */}
      {selectedPlan && (
        <div
          style={{
            marginTop: '20px',
            background: 'var(--cp-bg-surface-elevated)',
            border: '1px solid var(--cp-border-focus)',
            borderRadius: '16px',
            padding: '16px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 700 }}>
              {selectedPlan} ta'rifiga toʻlov qilish
            </h3>
            <button
              onClick={() => setSelectedPlan(null)}
              style={{ background: 'transparent', border: 'none', color: 'var(--cp-text-muted)', cursor: 'pointer', fontSize: '16px' }}
            >
              ✕
            </button>
          </div>

          <p style={{ margin: '0 0 12px 0', fontSize: '12px', color: 'var(--cp-text-muted)' }}>
            Quyidagi karta raqamiga toʻlovni bajaring va chek raqamini yozib yuboring:
          </p>

          <div
            style={{
              background: 'var(--cp-bg-surface)',
              borderRadius: '10px',
              padding: '12px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '14px',
            }}
          >
            <div>
              <div style={{ fontSize: '15px', fontWeight: 700, letterSpacing: '0.05em' }}>
                {instructions.card_number || '8600 0000 0000 0000'}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--cp-text-muted)', marginTop: '2px' }}>
                {instructions.card_holder || 'CryptoPulse Inc.'}
              </div>
            </div>
            <button
              className="btn btn-secondary"
              style={{ padding: '6px 10px', fontSize: '11px' }}
              onClick={() => handleCopyCard(instructions.card_number || '')}
            >
              {copied ? 'Nusxalandi!' : <><Copy size={13} style={{ marginRight: '4px' }} /> Nusxa</>}
            </button>
          </div>

          <form onSubmit={handleSubmitPayment}>
            <div style={{ marginBottom: '12px' }}>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--cp-text-muted)', marginBottom: '4px' }}>
                Toʻlov cheki raqami yoki tranzaksiya ID:
              </label>
              <input
                type="text"
                className="input"
                placeholder="Masalan: 123456789 yoki Payme chek kodi"
                value={reference}
                onChange={(e) => setReference(e.target.value)}
                required
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: '100%', justifyContent: 'center' }}
              disabled={submitting || !reference.trim()}
            >
              <Send size={15} style={{ marginRight: '6px' }} />
              {submitting ? 'Yuborilmoqda...' : 'Chekni yuborish'}
            </button>
          </form>
        </div>
      )}
    </div>
  );
};
