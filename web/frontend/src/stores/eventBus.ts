import { defineStore } from 'pinia';
import { ref } from 'vue';

export interface AppEvent {
  id: string; // Unique ID for the event
  name: 'highlight-item-in-list';
  payload: {
    itemType: string;
    id: string;
  };
  consumed: boolean;
}

export const useEventBusStore = defineStore('eventBus', () => {
  const events = ref<AppEvent[]>([]);

  function emit(name: AppEvent['name'], payload: AppEvent['payload']) {
    const event: AppEvent = {
      id: `${Date.now()}-${Math.random()}`,
      name,
      payload,
      consumed: false,
    };
    events.value.push(event);
  }

  function consume(eventId: string) {
    const event = events.value.find(e => e.id === eventId);
    if (event) {
      event.consumed = true;
    }
    // Clean up consumed events
    events.value = events.value.filter(e => !e.consumed);
  }

  return {
    events,
    emit,
    consume,
  };
});