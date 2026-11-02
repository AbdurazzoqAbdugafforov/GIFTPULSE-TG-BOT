import { useEffect, useState } from 'react';
import { TelegramWebApp } from '../telegram/webapp';

export function useTelegram() {
  const [isExpanded, setIsExpanded] = useState<boolean>(TelegramWebApp.isExpanded);
  const [user, setUser] = useState<any>(TelegramWebApp.user);
  const [isAvailable, setIsAvailable] = useState<boolean>(TelegramWebApp.isAvailable());

  useEffect(() => {
    // Notify Telegram that the app is ready to display
    TelegramWebApp.ready();

    // Listen to viewport changes
    const unsub = TelegramWebApp.onViewportChanged((_isStateStable) => {
      setIsExpanded(TelegramWebApp.isExpanded);
    });

    setUser(TelegramWebApp.user);
    setIsAvailable(TelegramWebApp.isAvailable());

    return () => {
      unsub();
    };
  }, []);

  const expand = () => {
    TelegramWebApp.expand();
    setIsExpanded(true);
    TelegramWebApp.haptic('light');
  };

  const close = () => {
    TelegramWebApp.close();
  };

  const haptic = (type?: any) => {
    TelegramWebApp.haptic(type);
  };

  return {
    isAvailable,
    isExpanded,
    user,
    expand,
    close,
    haptic,
  };
}
