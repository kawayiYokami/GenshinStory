const activeChildControllers = new Set<AbortController>();

export function registerChildSessionAbortController(controller: AbortController): void {
  activeChildControllers.add(controller);
}

export function unregisterChildSessionAbortController(controller: AbortController): void {
  activeChildControllers.delete(controller);
}

export function abortAllChildSessions(): void {
  for (const controller of activeChildControllers) {
    controller.abort();
  }
  activeChildControllers.clear();
}
