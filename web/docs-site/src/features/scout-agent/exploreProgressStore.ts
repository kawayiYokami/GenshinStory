import { reactive } from 'vue';

type ChildAgentStatus = 'queued' | 'running' | 'success' | 'partial' | 'failed' | 'timeout';

export interface ChildAgentProgress {
  task: string;
  usedCalls: number;
  latestTool: string;
  status: ChildAgentStatus;
  updatedAt: number;
}

export interface ExploreProgressSnapshot {
  sessionId: string;
  tasks: string[];
  startedAt: number;
  updatedAt: number;
  totalCalls: number;
  completed: boolean;
  childAgents: ChildAgentProgress[];
}

const state = reactive<{ sessions: Record<string, ExploreProgressSnapshot> }>({
  sessions: {},
});

function normalizedTaskKey(tasks: string[]): string {
  return tasks.map(item => String(item || '').trim()).filter(Boolean).join('||');
}

export function startExploreProgress(tasks: string[]): string {
  const now = Date.now();
  const sessionId = `explore_${now}_${Math.random().toString(36).slice(2, 8)}`;
  const cleanedTasks = tasks.map(item => String(item || '').trim()).filter(Boolean);
  const childAgents: ChildAgentProgress[] = cleanedTasks.map(task => ({
    task,
    usedCalls: 0,
    latestTool: '-',
    status: 'queued',
    updatedAt: now,
  }));

  state.sessions[sessionId] = {
    sessionId,
    tasks: cleanedTasks,
    startedAt: now,
    updatedAt: now,
    totalCalls: 0,
    completed: false,
    childAgents,
  };
  return sessionId;
}

export function markChildRunning(sessionId: string | undefined, task: string): void {
  if (!sessionId) return;
  const snapshot = state.sessions[sessionId];
  if (!snapshot || snapshot.completed) return;
  const target = snapshot.childAgents.find(item => item.task === task);
  if (!target) return;
  target.status = 'running';
  target.updatedAt = Date.now();
  snapshot.updatedAt = target.updatedAt;
}

export function recordChildToolCall(sessionId: string | undefined, task: string, toolName: string): void {
  if (!sessionId) return;
  const snapshot = state.sessions[sessionId];
  if (!snapshot || snapshot.completed) return;
  const target = snapshot.childAgents.find(item => item.task === task);
  if (!target) return;
  target.usedCalls += 1;
  target.latestTool = String(toolName || '-');
  target.status = 'running';
  target.updatedAt = Date.now();
  snapshot.totalCalls = snapshot.childAgents.reduce((sum, item) => sum + item.usedCalls, 0);
  snapshot.updatedAt = target.updatedAt;
}

export function markChildFinished(
  sessionId: string | undefined,
  task: string,
  status: ChildAgentStatus,
  finalCalls?: number,
): void {
  if (!sessionId) return;
  const snapshot = state.sessions[sessionId];
  if (!snapshot) return;
  const target = snapshot.childAgents.find(item => item.task === task);
  if (!target) return;
  if (typeof finalCalls === 'number' && Number.isFinite(finalCalls) && finalCalls >= 0) {
    target.usedCalls = Math.floor(finalCalls);
  }
  target.status = status;
  target.updatedAt = Date.now();
  snapshot.totalCalls = snapshot.childAgents.reduce((sum, item) => sum + item.usedCalls, 0);
  snapshot.updatedAt = target.updatedAt;
}

export function finishExploreProgress(sessionId: string | undefined): void {
  if (!sessionId) return;
  const snapshot = state.sessions[sessionId];
  if (!snapshot) return;
  snapshot.completed = true;
  snapshot.updatedAt = Date.now();

  setTimeout(() => {
    delete state.sessions[sessionId];
  }, 2 * 60 * 1000);
}

export function findActiveExploreProgressByTasks(tasks: string[]): ExploreProgressSnapshot | null {
  const key = normalizedTaskKey(tasks);
  if (!key) return null;
  const sessions = Object.values(state.sessions)
    .filter(item => !item.completed && normalizedTaskKey(item.tasks) === key)
    .sort((a, b) => b.startedAt - a.startedAt);
  return sessions[0] || null;
}

export function getExploreProgressState() {
  return state;
}

