import type {
  LLMSettingsCreateSchema,
  LLMSettingsUpdateSchema,
} from '@/lib/api-client';
import { LlmService } from '@/lib/api-client';
import { CreateLLMSettings, LLMSettings } from '@/types/api';

export interface LLMSettingsError {
  message: string;
  status?: number;
}

// All methods now use the generated client
export const fetchSettings = async (): Promise<LLMSettings> => {
  const data = await LlmService.getLlmSettingsApiV1LlmSettingsGet();

  // Transform generated schema to match current interface
  return {
    id: data.id,
    provider: data.provider,
    openai_model: data.openai_model || '',
    openrouter_model: data.openrouter_model || '',
    bedrock_model: data.bedrock_model || '',
    lmstudio_model: data.lmstudio_model || '',
  };
};

export const updateSettings = async (
  payload: Partial<LLMSettings>
): Promise<LLMSettings> => {
  // Transform current interface to generated schema
  const updatePayload: LLMSettingsUpdateSchema = {
    provider: payload.provider as LLMSettingsUpdateSchema['provider'],
    openai_model: payload.openai_model || null,
    openrouter_model: payload.openrouter_model || null,
    bedrock_model: payload.bedrock_model || null,
    lmstudio_model: payload.lmstudio_model || null,
  };

  const data = await LlmService.updateLlmSettingsApiV1LlmSettingsPatch({
    requestBody: updatePayload,
  });

  // Transform generated schema to match current interface
  return {
    id: data.id,
    provider: data.provider,
    openai_model: data.openai_model || '',
    openrouter_model: data.openrouter_model || '',
    bedrock_model: data.bedrock_model || '',
    lmstudio_model: data.lmstudio_model || '',
  };
};

export const createSettings = async (
  payload: CreateLLMSettings
): Promise<LLMSettings> => {
  // Transform current interface to generated schema
  const createPayload: LLMSettingsCreateSchema = {
    provider: payload.provider as LLMSettingsCreateSchema['provider'],
    openai_model: payload.openai_model || null,
    openrouter_model: payload.openrouter_model || null,
    bedrock_model: payload.bedrock_model || null,
    lmstudio_model: payload.lmstudio_model || null,
  };

  const data = await LlmService.createLlmSettingsApiV1LlmSettingsPost({
    requestBody: createPayload,
  });

  // Transform generated schema to match current interface
  return {
    id: data.id,
    provider: data.provider,
    openai_model: data.openai_model || '',
    openrouter_model: data.openrouter_model || '',
    bedrock_model: data.bedrock_model || '',
    lmstudio_model: data.lmstudio_model || '',
  };
};

export const fetchLMStudioModels = async (): Promise<string[]> => {
  return await LlmService.getLmstudioModelsApiV1LlmSettingsLmstudioModelsGet();
};
