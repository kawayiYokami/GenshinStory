import type { MemoryRecord, MemoryMatch } from './memoryStoreService';
import { isBackendMode } from '@/lib/searchProvider';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '/api';
const API_BASE = BACKEND_URL.endsWith('/api') ? BACKEND_URL : `${BACKEND_URL}/api`;

interface WorldTreeRecallResponse {
  total: number;
  records: MemoryRecord[];
}

class WorldTreeMemoryService {
  public isEnabled(): boolean {
    return isBackendMode();
  }

  public async recall(query: string, topK = 5): Promise<MemoryMatch[]> {
    if (!this.isEnabled()) return [];
    const normalized = String(query || '').trim();
    if (!normalized) return [];

    try {
      const params = new URLSearchParams({
        query: normalized,
        topK: String(Math.max(1, Math.floor(topK))),
      });

      const response = await fetch(`${API_BASE}/world-tree/recall?${params}`);
      if (!response.ok) return [];

      const payload = await response.json() as WorldTreeRecallResponse;
      const records = Array.isArray(payload.records) ? payload.records : [];
      return records.map((record, index) => ({
        record,
        hitCount: 1,
        lastHitTurnIndex: index,
      }));
    } catch (error) {
      console.error('[worldTreeMemoryService] recall failed:', error);
      return [];
    }
  }

  public async upsert(record: MemoryRecord): Promise<boolean> {
    if (!this.isEnabled()) return false;
    if (record.memoryType !== 'world_tree') return false;

    try {
      const response = await fetch(`${API_BASE}/world-tree/memory`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(record),
      });
      return response.ok;
    } catch (error) {
      console.error('[worldTreeMemoryService] upsert failed:', error);
      return false;
    }
  }

  public async remove(id: string): Promise<boolean> {
    if (!this.isEnabled()) return false;
    const normalized = String(id || '').trim();
    if (!normalized) return false;

    try {
      const response = await fetch(`${API_BASE}/world-tree/memory/${encodeURIComponent(normalized)}`, {
        method: 'DELETE',
      });
      return response.ok;
    } catch (error) {
      console.error('[worldTreeMemoryService] remove failed:', error);
      return false;
    }
  }
}

export const worldTreeMemoryService = new WorldTreeMemoryService();
export default worldTreeMemoryService;
