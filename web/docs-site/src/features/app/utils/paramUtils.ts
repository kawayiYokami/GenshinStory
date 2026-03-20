import logger from '@/features/app/services/loggerService';
import type { CustomParam } from '@/features/app/stores/config';

/**
 * 将用户输入的字符串值转换为合适的JavaScript类型
 * @param value 用户输入的字符串值
 * @returns 转换后的值（可能是 boolean, number, object, 或原始 string）
 */
function convertParamValue(value: string): any {
    if (!value || value.trim() === '') {
        return value;
    }

    // 布尔值转换
    if (value === 'true') return true;
    if (value === 'false') return false;

    // 数字转换
    // 数字转换（仅限标准数字格式）
    const trimmedValue = value.trim();
    if (/^-?\d+(\.\d+)?$/.test(trimmedValue)) {
        return Number(trimmedValue);
    }

    // JSON 尝试解析（用于数组和对象）
    try {
        return JSON.parse(value);
    } catch {
        return value;
    }
}

/**
 * 验证自定义参数的键名是否有效
 * @param key 参数键名
 * @returns 是否为有效键名
 */
function isValidParamKey(key: string): boolean {
    if (!key || key.trim() === '') return false;

    // 检查是否与保留字段冲突
    const reservedKeys = [
        'model', 'messages', 'temperature', 'stream', 'max_tokens',
        'apiUrl', 'apiKey', 'modelName', 'maxContextLength', 'requestInterval'
    ];

    return !reservedKeys.includes(key);
}

/**
 * 清理和验证自定义参数数组
 * @param params 自定义参数数组
 * @returns 清理后的参数数组
 */
function cleanCustomParams(params: CustomParam[] | undefined): CustomParam[] {
    if (!params) return [];

    return params
        .filter(param =>
            param.key &&
            param.value !== undefined &&
            param.value !== null &&
            param.value.trim().length > 0 &&
            isValidParamKey(param.key)
        )
        .map(param => ({
            key: param.key.trim(),
            value: param.value.trim()
        }));
}

/**
 * 将自定义参数转换为请求体对象
 * @param params 自定义参数数组
 * @returns 键值对对象
 */
export function paramsToRequestBody(params: CustomParam[] | undefined): Record<string, any> {
    const cleanedParams = cleanCustomParams(params);
    const result: Record<string, any> = {};

    for (const param of cleanedParams) {
        try {
            const convertedValue = convertParamValue(param.value);
            result[param.key] = convertedValue;
            logger.log(`参数转换成功: ${param.key} = ${JSON.stringify(convertedValue)}`);
        } catch (error) {
            logger.error(`参数转换失败: ${param.key} = ${param.value}, 错误:`, error);
            result[param.key] = param.value; // 失败时使用原始值
        }
    }

    return result;
}