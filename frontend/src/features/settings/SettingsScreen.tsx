import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { TelegramWebApp } from '../../telegram/webapp';
import { Globe, Clock, Bell, Trash2, CheckCircle2, AlertTriangle, Shield } from 'lucide-react';

interface SettingsData {
  language: string;
  timezone: string;
  daily_summary_enabled: boolean;
}

export const SettingsScreen: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [settings, setSettings] = useState<SettingsData>({
    language: 'uz',
    timezone: 'Asia/Tashkent',
    daily_summary_enabled: true,
  });
  const [userProfile, setUserProfile] = useState<any>(null);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const [stgRes, meRes] = await Promise.all([
          api.getSettings(),
          api.getMe().catch(() => null),
        ]);
        if (stgRes) setSettings(stgRes);
        if (meRes?.user) setUserProfile(meRes.user);
      } catch (e) {
        console.error('Failed to load settings', e);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const handleUpdate = async (field: keyof SettingsData, value: any) => {
    const updated = { ...settings, [field]: value };
    setSettings(updated);
    TelegramWebApp.haptic('selection');

    try {
      setSaving(true);
      await api.updateSettings({ [field]: value });
      setStatusMsg('Sozlamalar saqlandi');
      setTimeout(() => setStatusMsg(null), 2500);
    } catch (e: any) {
      console.error('Failed to update settings', e);
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteData = async () => {
    try {
      setDeleting(true);
      await api.deleteMyData();
      TelegramWebApp.haptic('warning');
      TelegramWebApp.close();
    } catch (err: any) {
      console.error('Failed to delete data', err);
      setDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

  if (loading) {
    return (
      <div className="empty-state">
        <div className="spinner" />
        <p>Sozlamalar yuklanmoqda...</p>
      </div>
    );
  }

  return (
    <div style={{ paddingBottom: '36px' }}>
      <div style={{ marginBottom: '16px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: 700, margin: '0 0 4px 0' }}>Sozlamalar</h2>
        <p style={{ margin: 0, fontSize: '13px', color: 'var(--cp-text-muted)' }}>
          Ilova tili, vaqt mintaqasi va bildirishnomalarni boshqaring
        </p>
      </div>

      {statusMsg && (
        <div
          style={{
            background: 'rgba(34, 197, 94, 0.15)',
            border: '1px solid rgba(34, 197, 94, 0.3)',
            borderRadius: '10px',
            padding: '10px 14px',
            fontSize: '13px',
            color: 'var(--cp-success)',
            marginBottom: '14px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <CheckCircle2 size={16} />
          <span>{statusMsg}</span>
        </div>
      )}

      {/* User info card */}
      {userProfile && (
        <div className="card" style={{ marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                width: '44px',
                height: '44px',
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #38bdf8 0%, #1e40af 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 700,
                fontSize: '18px',
              }}
            >
              {userProfile.first_name ? userProfile.first_name[0].toUpperCase() : 'U'}
            </div>
            <div>
              <div style={{ fontSize: '15px', fontWeight: 700 }}>{userProfile.first_name}</div>
              <div style={{ fontSize: '12px', color: 'var(--cp-text-muted)' }}>
                {userProfile.username ? `@${userProfile.username}` : `ID: ${userProfile.telegram_id}`}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Preferences Section */}
      <div className="card" style={{ marginBottom: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* Language */}
        <div>
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>
            <Globe size={16} color="var(--cp-brand)" />
            <span>Ilova tili</span>
          </label>
          <select
            className="input"
            value={settings.language}
            onChange={(e) => handleUpdate('language', e.target.value)}
            disabled={saving}
          >
            <option value="uz">Oʻzbekcha (UZ)</option>
            <option value="en">English (EN)</option>
            <option value="ru">Русский (RU)</option>
          </select>
        </div>

        {/* Timezone */}
        <div>
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>
            <Clock size={16} color="var(--cp-brand)" />
            <span>Vaqt mintaqasi (Timezone)</span>
          </label>
          <select
            className="input"
            value={settings.timezone}
            onChange={(e) => handleUpdate('timezone', e.target.value)}
            disabled={saving}
          >
            <option value="Asia/Tashkent">Toshkent (UTC+5)</option>
            <option value="UTC">UTC (Dunyo vaqti)</option>
            <option value="Europe/Istanbul">Istanbul (UTC+3)</option>
            <option value="Europe/Moscow">Moskva (UTC+3)</option>
            <option value="Asia/Dubai">Dubay (UTC+4)</option>
            <option value="America/New_York">Nyu-York (UTC-5)</option>
          </select>
        </div>

        {/* Daily Summary */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '4px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', fontWeight: 600 }}>
              <Bell size={16} color="var(--cp-brand)" />
              <span>Kunlik bozor xabarnomasi</span>
            </div>
            <div style={{ fontSize: '12px', color: 'var(--cp-text-muted)', marginTop: '2px' }}>
              Har tong soat 08:00 da Telegram orqali qisqacha bozor holati
            </div>
          </div>
          <input
            type="checkbox"
            checked={settings.daily_summary_enabled}
            onChange={(e) => handleUpdate('daily_summary_enabled', e.target.checked)}
            style={{ width: '18px', height: '18px', accentColor: 'var(--cp-brand)', cursor: 'pointer' }}
          />
        </div>
      </div>

      {/* Security and Privacy */}
      <div className="card" style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px', fontWeight: 700, marginBottom: '8px' }}>
          <Shield size={16} color="var(--cp-brand)" />
          <span>Maxfiylik va Xavfsizlik</span>
        </div>
        <p style={{ fontSize: '12px', color: 'var(--cp-text-muted)', margin: '0 0 14px 0', lineHeight: 1.5 }}>
          CryptoPulse sizning hisoblaringizga yoki hamyonlaringizga ulanmaydi. Barcha maʼlumotlar xavfsiz saqlanadi.
        </p>

        {!showDeleteConfirm ? (
          <button
            className="btn btn-danger"
            style={{ width: '100%', justifyContent: 'center', fontSize: '12px' }}
            onClick={() => setShowDeleteConfirm(true)}
          >
            <Trash2 size={14} style={{ marginRight: '6px' }} />
            Barcha shaxsiy maʼlumotlarimni oʻchirish
          </button>
        ) : (
          <div
            style={{
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '10px',
              padding: '12px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--cp-danger)', fontWeight: 700, fontSize: '13px', marginBottom: '6px' }}>
              <AlertTriangle size={16} />
              <span>Haqiqatan ham oʻchirmoqchimisiz?</span>
            </div>
            <p style={{ fontSize: '12px', color: 'var(--cp-text-muted)', margin: '0 0 10px 0' }}>
              Barcha narx signallaringiz, kuzatuv roʻyxatingiz va portfelingiz qaytarib boʻlmas darajada oʻchiriladi.
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              <button
                className="btn btn-secondary"
                style={{ justifyContent: 'center' }}
                onClick={() => setShowDeleteConfirm(false)}
                disabled={deleting}
              >
                Bekor qilish
              </button>
              <button
                className="btn btn-danger"
                style={{ justifyContent: 'center' }}
                onClick={handleDeleteData}
                disabled={deleting}
              >
                {deleting ? 'Oʻchirilmoqda...' : 'Ha, oʻchirish'}
              </button>
            </div>
          </div>
        )}
      </div>

      <div style={{ textAlign: 'center', fontSize: '11px', color: 'var(--cp-text-muted)' }}>
        CryptoPulse v1.2.0 • Telegram Mini App
      </div>
    </div>
  );
};
