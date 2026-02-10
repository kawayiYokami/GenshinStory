export interface AskChoiceUiProtocol {
  type: 'ask_choice';
  question: string;
  suggestions: string[];
}

export type UiProtocolPayload = AskChoiceUiProtocol;

