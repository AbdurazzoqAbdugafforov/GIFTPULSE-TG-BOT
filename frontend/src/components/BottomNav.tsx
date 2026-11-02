import React from 'react';
import { Home, Store, Bell, Briefcase, Compass } from 'lucide-react';
import { TabType } from '../types';
import { TelegramWebApp } from '../telegram/webapp';

interface BottomNavProps {
  currentTab: TabType;
  onTabChange: (tab: TabType) => void;
  alertsCount?: number;
}

interface NavItem {
  id: TabType;
  label: string;
  icon: React.ComponentType<{ size?: number | string }>;
  badge?: number;
}

export const BottomNav: React.FC<BottomNavProps> = ({ currentTab, onTabChange, alertsCount }) => {
  const tabs: NavItem[] = [
    { id: 'dashboard', label: 'Bosh sahifa', icon: Home },
    { id: 'markets', label: 'Bozor', icon: Store },
    { id: 'radar', label: 'Radar', icon: Compass },
    { id: 'alerts', label: 'Signallar', icon: Bell, badge: alertsCount },
    { id: 'portfolio', label: 'Portfel', icon: Briefcase },
  ];

  const handleSelect = (tab: TabType) => {
    TelegramWebApp.hapticFeedback('selection');
    onTabChange(tab);
  };

  return (
    <nav className="bottom-nav">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const isActive = currentTab === tab.id;
        return (
          <button
            key={tab.id}
            className={`nav-item ${isActive ? 'active' : ''}`}
            onClick={() => handleSelect(tab.id)}
          >
            <div className="icon-wrap">
              <Icon size={20} />
              {tab.badge && tab.badge > 0 ? <span className="nav-badge">{tab.badge}</span> : null}
            </div>
            <span className="nav-label">{tab.label}</span>
          </button>
        );
      })}
    </nav>
  );
};
