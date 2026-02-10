import type { UiProtocolPayload } from './types';

class UiProtocolService {
  public parse(payload: { name: string; args: Record<string, any> }): UiProtocolPayload | null {
    const { name, args } = payload;

    if (name === 'ask_choice') {
      const question = String(args?.question || '').trim();
      const suggestions = Array.isArray(args?.suggestions)
        ? args.suggestions.map((item: unknown) => String(item)).filter(Boolean)
        : (Array.isArray(args?.suggest)
          ? args.suggest.map((item: unknown) => String(item)).filter(Boolean)
          : (args?.suggest ? [String(args.suggest)] : []));

      return {
        type: 'ask_choice',
        question,
        suggestions,
      };
    }

    return null;
  }
}

export const uiProtocolService = new UiProtocolService();
export default uiProtocolService;

