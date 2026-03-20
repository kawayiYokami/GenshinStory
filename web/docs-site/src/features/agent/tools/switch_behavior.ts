import type { Tool, ToolExecutionResult } from './tool';
import logger from '@/features/app/services/loggerService';
import { useAgentStore } from '@/features/agent/stores/agentStore';
import promptService from '@/features/agent/tools/implementations/promptService';

interface SwitchBehaviorParams {
  instructionId?: string;
  reason?: string;
}

const INSTRUCTION_ID_ALIASES: Record<string, string> = {
  interrogation: 'search',
};

const switchBehaviorTool: Tool<SwitchBehaviorParams> = {
  name: 'switch_behavior',
  type: 'execution',
  description: '',
  usage: '',
  examples: [],
  error_guidance: '',

  async execute(params: SwitchBehaviorParams): Promise<ToolExecutionResult> {
    try {
      const targetInstructionId = String(params.instructionId || '').trim();
      if (!targetInstructionId) {
        return {
          result: "错误: switch_behavior 缺少 instructionId 参数。",
        };
      }
      const normalizedTargetInstructionId = INSTRUCTION_ID_ALIASES[targetInstructionId] || targetInstructionId;

      const instructions = await promptService.listAvailableInstructions();
      const target = instructions.find(item => item.id === normalizedTargetInstructionId);
      if (!target) {
        return {
          result: JSON.stringify({
            tool: 'switch_behavior',
            status: 'rejected',
            reason: `未找到行为: ${normalizedTargetInstructionId}`,
            availableInstructionIds: instructions.map(item => item.id),
          }, null, 2),
        };
      }

      const agentStore = useAgentStore();
      const currentInstructionIdRaw = (agentStore as any).currentInstructionId;
      const currentInstructionId = typeof currentInstructionIdRaw === 'string'
        ? currentInstructionIdRaw.trim()
        : String(currentInstructionIdRaw?.value || '').trim();
      if (currentInstructionId === normalizedTargetInstructionId) {
        return {
          result: JSON.stringify({
            tool: 'switch_behavior',
            status: 'noop',
            instructionId: normalizedTargetInstructionId,
            message: '当前已是目标行为，无需切换。',
          }, null, 2),
        };
      }

      await agentStore.setInstruction(normalizedTargetInstructionId);

      logger.log('[switch_behavior] 行为已切换', {
        from: currentInstructionId,
        to: normalizedTargetInstructionId,
        reason: String(params.reason || '').trim(),
      });

      return {
        result: JSON.stringify({
          tool: 'switch_behavior',
          status: 'switched',
          instructionId: normalizedTargetInstructionId,
          instructionName: target.name,
          message: '行为切换成功，将在后续轮次生效。',
        }, null, 2),
      };
    } catch (error: any) {
      logger.error("工具 switch_behavior 发生意外异常:", error);
      return {
        result: "错误: 工具 'switch_behavior' 内部执行失败。",
      };
    }
  },
};

export default switchBehaviorTool;
