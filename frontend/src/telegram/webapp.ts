/**
 * Telegram WebApp Integration Wrapper with safe fallback for standalone browser testing.
 */

declare global {
  interface Window {
    Telegram?: {
      WebApp: any;
    };
  }
}

export type HapticType = 'light' | 'medium' | 'heavy' | 'success' | 'warning' | 'error' | 'selection';

export class TelegramWebApp {
  private static get webApp() {
    return typeof window !== 'undefined' ? window.Telegram?.WebApp : undefined;
  }

  public static isAvailable(): boolean {
    return !!this.webApp && !!this.webApp.initData;
  }

  public static get initData(): string {
    return this.webApp?.initData || '';
  }

  public static get initDataUnsafe(): any {
    return this.webApp?.initDataUnsafe || {};
  }

  public static get user(): any {
    return this.webApp?.initDataUnsafe?.user || null;
  }

  public static get isExpanded(): boolean {
    return this.webApp?.isExpanded ?? true;
  }

  public static get viewportHeight(): number {
    return this.webApp?.viewportHeight || (typeof window !== 'undefined' ? window.innerHeight : 600);
  }

  public static get viewportStableHeight(): number {
    return this.webApp?.viewportStableHeight || (typeof window !== 'undefined' ? window.innerHeight : 600);
  }

  public static ready(): void {
    try {
      this.webApp?.ready();
    } catch (e) {
      console.warn('Telegram WebApp ready error:', e);
    }
  }

  public static expand(): void {
    try {
      this.webApp?.expand();
    } catch (e) {
      console.warn('Telegram WebApp expand error:', e);
    }
  }

  public static close(): void {
    try {
      this.webApp?.close();
    } catch (e) {
      console.warn('Telegram WebApp close error:', e);
    }
  }

  public static setHeaderColor(color: string): void {
    try {
      this.webApp?.setHeaderColor?.(color);
    } catch (e) {
      // ignore
    }
  }

  public static setBackgroundColor(color: string): void {
    try {
      this.webApp?.setBackgroundColor?.(color);
    } catch (e) {
      // ignore
    }
  }

  public static hapticFeedback(type: HapticType = 'light'): void {
    this.haptic(type);
  }

  public static haptic(type: HapticType = 'light'): void {
    try {
      if (type === 'selection') {
        this.webApp?.HapticFeedback?.selectionChanged();
      } else if (['success', 'warning', 'error'].includes(type)) {
        this.webApp?.HapticFeedback?.notificationOccurred(type);
      } else {
        this.webApp?.HapticFeedback?.impactOccurred(type);
      }
    } catch (e) {
      // Haptics fail silently on desktop
    }
  }

  private static currentBackHandler: (() => void) | null = null;

  public static showBackButton(onClick: () => void): void {
    const bb = this.webApp?.BackButton;
    if (!bb) return;

    if (this.currentBackHandler) {
      bb.offClick(this.currentBackHandler);
    }
    this.currentBackHandler = onClick;
    bb.onClick(onClick);
    bb.show();
  }

  public static hideBackButton(): void {
    const bb = this.webApp?.BackButton;
    if (!bb) return;

    if (this.currentBackHandler) {
      bb.offClick(this.currentBackHandler);
      this.currentBackHandler = null;
    }
    bb.hide();
  }

  public static setupBackButton(onClick: () => void): () => void {
    this.showBackButton(onClick);
    return () => this.hideBackButton();
  }

  public static onViewportChanged(callback: (isStateStable: boolean) => void): () => void {
    const wa = this.webApp;
    if (!wa) return () => {};

    wa.onEvent('viewportChanged', callback);
    return () => {
      wa.offEvent('viewportChanged', callback);
    };
  }
}
