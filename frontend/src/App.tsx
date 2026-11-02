import React, { useState, useEffect, useCallback } from 'react';
import { TabType, DashboardData } from './types';
import { api } from './services/api';
import { TelegramWebApp } from './telegram/webapp';
import { Header } from './components/Header';
import { BottomNav } from './components/BottomNav';

// Feature screens
import { DashboardScreen } from './features/dashboard/DashboardScreen';
import { MarketsScreen } from './features/markets/MarketsScreen';
import { AlertsScreen } from './features/alerts/AlertsScreen';
import { PortfolioScreen } from './features/portfolio/PortfolioScreen';
import { RadarScreen } from './features/radar/RadarScreen';
import { IndexScreen } from './features/index/IndexScreen';
import { SubscriptionScreen } from './features/subscriptions/SubscriptionScreen';
import { SettingsScreen } from './features/settings/SettingsScreen';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);
  const [alertPrefill, setAlertPrefill] = useState<{ id: number; name: string } | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Initialize Telegram WebApp & Auth
  useEffect(() => {
    TelegramWebApp.ready();
    TelegramWebApp.setHeaderColor('#0f172a');
    TelegramWebApp.setBackgroundColor('#0f172a');

    const init = async () => {
      try {
        setLoading(true);
        // Attempt Telegram initData auth
        await api.authenticateWithTelegram();
        // Fetch dashboard overview
        const dash = await api.getDashboard();
        setDashboardData(dash);
      } catch (err) {
        console.warn('Dashboard init error:', err);
      } finally {
        setLoading(false);
      }
    };

    init();
  }, []);

  // Back button handling
  useEffect(() => {
    if (activeTab !== 'dashboard' || selectedSlug) {
      TelegramWebApp.showBackButton(() => {
        if (selectedSlug) {
          setSelectedSlug(null);
        } else {
          setActiveTab('dashboard');
        }
      });
    } else {
      TelegramWebApp.hideBackButton();
    }

    return () => {
      TelegramWebApp.hideBackButton();
    };
  }, [activeTab, selectedSlug]);

  const handleNavigate = useCallback((tab: TabType) => {
    TelegramWebApp.hapticFeedback('selection');
    setActiveTab(tab);
    if (tab !== 'markets') {
      setSelectedSlug(null);
    }
  }, []);

  const handleSelectCollection = useCallback((slug: string) => {
    setSelectedSlug(slug);
    setActiveTab('markets');
    TelegramWebApp.hapticFeedback('selection');
  }, []);

  const handleCreateAlert = useCallback((colId: number, colName: string) => {
    setAlertPrefill({ id: colId, name: colName });
    setActiveTab('alerts');
    TelegramWebApp.hapticFeedback('selection');
  }, []);

  return (
    <div className="app-container">
      <Header
        indexValue={dashboardData?.index.value}
        indexChange={dashboardData?.index.change_1d_pct}
        dataFreshness={dashboardData?.data_freshness}
      />

      <main className="content-area">
        {activeTab === 'dashboard' && (
          <DashboardScreen
            onNavigate={handleNavigate}
            onSelectCollection={handleSelectCollection}
          />
        )}

        {activeTab === 'markets' && (
          <MarketsScreen
            selectedSlug={selectedSlug}
            onClearSlug={() => setSelectedSlug(null)}
            onCreateAlert={handleCreateAlert}
          />
        )}

        {activeTab === 'alerts' && (
          <AlertsScreen
            initialCollectionId={alertPrefill?.id}
            initialCollectionName={alertPrefill?.name}
            onClearInitial={() => setAlertPrefill(null)}
          />
        )}

        {activeTab === 'portfolio' && <PortfolioScreen />}

        {activeTab === 'radar' && (
          <RadarScreen onSelectCollection={handleSelectCollection} />
        )}

        {activeTab === 'index' && (
          <IndexScreen
            onBack={() => setActiveTab('dashboard')}
            onSelectCollection={handleSelectCollection}
          />
        )}

        {activeTab === 'subscriptions' && <SubscriptionScreen />}

        {activeTab === 'settings' && <SettingsScreen />}
      </main>

      <BottomNav
        currentTab={activeTab}
        onTabChange={handleNavigate}
        alertsCount={dashboardData?.active_alerts_count}
      />
    </div>
  );
};

export default App;
