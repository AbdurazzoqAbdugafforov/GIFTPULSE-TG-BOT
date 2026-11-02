/**
 * API client for GiftPulse backend with Telegram initData HMAC authentication.
 */

import { TelegramWebApp } from '../telegram/webapp';
import {
  AlertItem,
  DashboardData,
  GiftCollection,
  GiftModel,
  PortfolioSummary,
  RadarData,
  TGGIIndex,
  UserProfile,
} from '../types';

const API_BASE = '/api/v1';

class ApiClient {
  private token: string | null = null;

  constructor() {
    this.token = typeof localStorage !== 'undefined' ? localStorage.getItem('gp_token') : null;
  }

  public setToken(token: string) {
    this.token = token;
    localStorage.setItem('gp_token', token);
  }

  public clearToken() {
    this.token = null;
    localStorage.removeItem('gp_token');
  }

  private async fetchWithAuth(endpoint: string, options: RequestInit = {}): Promise<any> {
    if (!this.token) {
      await this.ensureAuth();
    }

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    let response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    // If 401 Unauthorized, re-authenticate and retry
    if (response.status === 401) {
      this.clearToken();
      const authSuccess = await this.ensureAuth();
      if (authSuccess && this.token) {
        headers['Authorization'] = `Bearer ${this.token}`;
        response = await fetch(`${API_BASE}${endpoint}`, {
          ...options,
          headers,
        });
      }
    }

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `HTTP Error ${response.status}`);
    }

    return response.json();
  }

  public async authenticateWithTelegram(): Promise<boolean> {
    const initData = TelegramWebApp.initData;
    if (!initData) return false;

    try {
      const res = await fetch(`${API_BASE}/auth/telegram`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ init_data: initData }),
      });

      if (res.ok) {
        const data = await res.json();
        if (data.token) {
          this.setToken(data.token);
          return true;
        }
      }
    } catch (e) {
      console.error('Telegram auth failed:', e);
    }
    return false;
  }

  public async authenticateGuest(): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/auth/guest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });

      if (res.ok) {
        const data = await res.json();
        if (data.token) {
          this.setToken(data.token);
          return true;
        }
      }
    } catch (e) {
      console.error('Guest auth failed:', e);
    }
    return false;
  }

  public async ensureAuth(): Promise<boolean> {
    if (this.token) return true;
    if (TelegramWebApp.initData) {
      const success = await this.authenticateWithTelegram();
      if (success) return true;
    }
    return this.authenticateGuest();
  }

  public async getMe(): Promise<any> {
    return this.fetchWithAuth('/auth/me');
  }

  // Dashboard
  public async getDashboard(): Promise<DashboardData> {
    return this.fetchWithAuth('/dashboard');
  }

  // Collections & Market
  public async getCollections(
    search?: string,
    sortBy: string = 'floor_desc',
    limit: number = 50,
    offset: number = 0
  ): Promise<{ items: GiftCollection[]; total: number; attribution: string; attribution_url: string }> {
    const params = new URLSearchParams({ sort_by: sortBy, limit: String(limit), offset: String(offset) });
    if (search) params.set('search', search);
    return this.fetchWithAuth(`/markets/collections?${params.toString()}`);
  }

  public async getCollection(slug: string): Promise<GiftCollection> {
    return this.fetchWithAuth(`/markets/collections/${slug}`);
  }

  public async getCollectionModels(
    slug: string,
    search?: string,
    sortBy: string = 'floor_desc',
    limit: number = 100
  ): Promise<{ collection: any; items: GiftModel[]; total: number }> {
    const params = new URLSearchParams({ sort_by: sortBy, limit: String(limit) });
    if (search) params.set('search', search);
    return this.fetchWithAuth(`/markets/collections/${slug}/models?${params.toString()}`);
  }

  public async getModel(modelId: number): Promise<GiftModel> {
    return this.fetchWithAuth(`/markets/models/${modelId}`);
  }

  public async getIndex(): Promise<TGGIIndex> {
    return this.fetchWithAuth('/markets/index');
  }

  // Radar
  public async getRadar(): Promise<RadarData> {
    return this.fetchWithAuth('/radar');
  }

  // Alerts
  public async getAlerts(): Promise<AlertItem[]> {
    return this.fetchWithAuth('/alerts');
  }

  public async createAlert(payload: {
    collection_id: number;
    model_id?: number | null;
    alert_type: string;
    target_value: number;
    is_recurring?: boolean;
  }): Promise<AlertItem> {
    return this.fetchWithAuth('/alerts', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  public async pauseAlert(id: number): Promise<{ status: string }> {
    return this.fetchWithAuth(`/alerts/${id}/pause`, { method: 'PUT' });
  }

  public async resumeAlert(id: number): Promise<{ status: string }> {
    return this.fetchWithAuth(`/alerts/${id}/resume`, { method: 'PUT' });
  }

  public async deleteAlert(id: number): Promise<{ status: string }> {
    return this.fetchWithAuth(`/alerts/${id}`, { method: 'DELETE' });
  }

  // Watchlist
  public async getWatchlist(): Promise<GiftCollection[]> {
    return this.fetchWithAuth('/watchlist');
  }

  public async addToWatchlist(collection_id: number): Promise<{ status: string }> {
    return this.fetchWithAuth('/watchlist', {
      method: 'POST',
      body: JSON.stringify({ collection_id }),
    });
  }

  public async removeFromWatchlist(collection_id: number): Promise<{ status: string }> {
    return this.fetchWithAuth(`/watchlist/${collection_id}`, { method: 'DELETE' });
  }

  // Portfolio
  public async getPortfolio(): Promise<PortfolioSummary> {
    return this.fetchWithAuth('/portfolio');
  }

  public async addPortfolioPosition(payload: {
    collection_id: number;
    model_id?: number | null;
    quantity: number;
    purchase_price: number;
    purchase_date?: string | null;
    notes?: string | null;
  }): Promise<any> {
    return this.fetchWithAuth('/portfolio', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  public async deletePortfolioPosition(id: number): Promise<{ status: string }> {
    return this.fetchWithAuth(`/portfolio/${id}`, { method: 'DELETE' });
  }

  // Subscription
  public async getSubscription(): Promise<any> {
    return this.fetchWithAuth('/subscription');
  }

  public async submitPayment(plan_code: string, transaction_reference: string): Promise<any> {
    return this.fetchWithAuth('/subscription/payment-request', {
      method: 'POST',
      body: JSON.stringify({ plan_code, transaction_reference }),
    });
  }

  // Settings
  public async getSettings(): Promise<any> {
    return this.fetchWithAuth('/settings');
  }

  public async updateSettings(payload: {
    language?: string;
    timezone?: string;
    daily_report_enabled?: boolean;
    notifications_enabled?: boolean;
  }): Promise<any> {
    return this.fetchWithAuth('/settings', {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  public async deleteMyData(): Promise<any> {
    return this.fetchWithAuth('/settings/delete-data', { method: 'POST' });
  }
}

export const api = new ApiClient();
