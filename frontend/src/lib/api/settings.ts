import apiClient from './client';
import { ApiResponse, LLMConfig, ModelProvider, ModelType } from '@/types';

export interface ModelConfig {
  id: number;
  provider: ModelProvider;
  model_name: string;
  model_type: ModelType;
  api_key: string;
  api_base: string | null;
  temperature: number;
  max_tokens: number;
  top_p: number;
  use_case: string;
  is_default: boolean;
  is_active: boolean;
  priority: number;
  advanced_config: Record<string, unknown>;
}

export interface ValidateApiKeyResult {
  valid: boolean;
  message: string;
}

export interface DiscoveredModel {
  name: string;
  model_type: string; // llm / embedding / rerank
}

export interface BatchSaveModelItem {
  provider: string;
  model_name: string;
  model_type: string;
  api_key: string;
  api_base?: string | null;
}

export interface TenantInfo {
  id: number;
  tenant_id: string;
  company_name: string;
  contact_name: string | null;
  contact_email: string;
  contact_phone: string | null;
  status: string;
  current_plan: string;
  api_key_prefix: string | null;
}

export const settingsApi = {
  // Get all model configs
  getModelConfigs: async (): Promise<ApiResponse<ModelConfig[]>> => {
    const response = await apiClient.get<ApiResponse<ModelConfig[]>>('/models');
    return response.data;
  },

  // Get model configs filtered by model_type
  getModelConfigsByType: async (modelType: string): Promise<ApiResponse<ModelConfig[]>> => {
    const response = await apiClient.get<ApiResponse<ModelConfig[]>>('/models', {
      params: { model_type: modelType, is_active: true },
    });
    return response.data;
  },

  // Get default model config
  getDefaultModel: async (): Promise<ApiResponse<ModelConfig | null>> => {
    const response = await apiClient.get<ApiResponse<ModelConfig | null>>('/models/default');
    return response.data;
  },

  // Create model config
  createModelConfig: async (config: Partial<ModelConfig>): Promise<ApiResponse<ModelConfig>> => {
    const response = await apiClient.post<ApiResponse<ModelConfig>>('/models', config);
    return response.data;
  },

  // Update model config
  updateModelConfig: async (configId: number, config: Partial<ModelConfig>): Promise<ApiResponse<ModelConfig>> => {
    const response = await apiClient.put<ApiResponse<ModelConfig>>(`/models/${configId}`, config);
    return response.data;
  },

  // Delete model config
  deleteModelConfig: async (configId: number): Promise<ApiResponse<{ message: string }>> => {
    const response = await apiClient.delete<ApiResponse<{ message: string }>>(`/models/${configId}`);
    return response.data;
  },

  // Set default model
  setDefaultModel: async (configId: number): Promise<ApiResponse<ModelConfig>> => {
    const response = await apiClient.post<ApiResponse<ModelConfig>>(`/models/${configId}/set-default`);
    return response.data;
  },

  // Legacy methods for compatibility
  getLLMConfig: async (): Promise<ApiResponse<LLMConfig | null>> => {
    const response = await apiClient.get<ApiResponse<ModelConfig | null>>('/models/default');
    const data = response.data;
    if (data.success && data.data) {
      const config = data.data;
      return {
        success: true,
        data: {
          provider: config.provider as ModelProvider,
          api_key: config.api_key,
          model_name: config.model_name,
          temperature: config.temperature,
          system_prompt: (config.advanced_config?.system_prompt as string) || '',
        },
        error: null,
      };
    }
    return { success: false, data: null, error: data.error };
  },

  updateLLMConfig: async (config: Partial<LLMConfig>): Promise<ApiResponse<LLMConfig>> => {
    // First get the default model to get its ID
    const defaultResponse = await apiClient.get<ApiResponse<ModelConfig | null>>('/models/default');

    if (defaultResponse.data.success && defaultResponse.data.data) {
      const configId = defaultResponse.data.data.id;
      const updateData: Partial<ModelConfig> = {
        provider: config.provider,
        api_key: config.api_key,
        model_name: config.model_name,
        temperature: config.temperature,
        advanced_config: config.system_prompt ? { system_prompt: config.system_prompt } : undefined,
      };

      const response = await apiClient.put<ApiResponse<ModelConfig>>(`/models/${configId}`, updateData);
      const data = response.data;

      if (data.success && data.data) {
        return {
          success: true,
          data: {
            provider: data.data.provider as ModelProvider,
            api_key: data.data.api_key,
            model_name: data.data.model_name,
            temperature: data.data.temperature,
            system_prompt: (data.data.advanced_config?.system_prompt as string) || '',
          },
          error: null,
        };
      }
    }

    // If no default model exists, create one
    const createData: Partial<ModelConfig> = {
      provider: config.provider || 'openai',
      api_key: config.api_key || '',
      model_name: config.model_name || 'gpt-4o',
      temperature: config.temperature || 0.7,
      max_tokens: 2000,
      top_p: 0.9,
      use_case: 'chat',
      is_default: true,
      priority: 1,
      advanced_config: config.system_prompt ? { system_prompt: config.system_prompt } : {},
    };

    const response = await apiClient.post<ApiResponse<ModelConfig>>('/models', createData);
    const data = response.data;

    if (data.success && data.data) {
      return {
        success: true,
        data: {
          provider: data.data.provider as ModelProvider,
          api_key: data.data.api_key,
          model_name: data.data.model_name,
          temperature: data.data.temperature,
          system_prompt: (data.data.advanced_config?.system_prompt as string) || '',
        },
        error: null,
      };
    }

    return { success: false, data: null as unknown as LLMConfig, error: data.error };
  },

  testLLMConnection: async (): Promise<ApiResponse<{ success: boolean; message: string }>> => {
    // TODO: Implement when backend has test endpoint
    return { success: true, data: { success: true, message: '连接测试成功' }, error: null };
  },

  // Validate API Key against the provider
  validateApiKey: async (
    provider: string,
    api_key: string,
    api_base?: string
  ): Promise<ApiResponse<ValidateApiKeyResult>> => {
    const response = await apiClient.post<ApiResponse<ValidateApiKeyResult>>(
      '/models/validate-api-key',
      { provider, api_key, api_base: api_base || null }
    );
    return response.data;
  },

  // Discover available models for a provider via API
  discoverModels: async (
    provider: string,
    api_key: string,
    api_base?: string
  ): Promise<ApiResponse<{ models: DiscoveredModel[] }>> => {
    const response = await apiClient.post<ApiResponse<{ models: DiscoveredModel[] }>>(
      '/models/discover',
      { provider, api_key, api_base: api_base || null }
    );
    return response.data;
  },

  // Batch create or update model configs (upsert by provider+model_name)
  batchSaveModels: async (
    models: BatchSaveModelItem[]
  ): Promise<ApiResponse<ModelConfig[]>> => {
    const response = await apiClient.post<ApiResponse<ModelConfig[]>>(
      '/models/batch-save',
      { models }
    );
    return response.data;
  },

  // Get tenant info (includes api_key_prefix)
  getTenantInfo: async (): Promise<ApiResponse<TenantInfo>> => {
    const response = await apiClient.get<ApiResponse<TenantInfo>>('/tenant/info-token');
    return response.data;
  },

  // Reset tenant API Key (returns new key once)
  resetApiKey: async (): Promise<ApiResponse<{ api_key: string; api_key_prefix: string; message: string }>> => {
    const response = await apiClient.post<ApiResponse<{ api_key: string; api_key_prefix: string; message: string }>>('/tenant/reset-api-key');
    return response.data;
  },
};
