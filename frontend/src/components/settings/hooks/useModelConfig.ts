import { useState, useEffect } from 'react';
import { message } from 'antd';
import { settingsApi, DiscoveredModel } from '@/lib/api/settings';
import { ModelProvider, ModelType } from '@/types';

interface PlatformConfig {
  api_key: string;
  api_base: string;
  llm_model: string;
  embedding_model: string;
  rerank_model: string;
  image_generation_model: string;
  video_generation_model: string;
  llm_id?: number;
  embedding_id?: number;
  rerank_id?: number;
  image_generation_id?: number;
  video_generation_id?: number;
}

type ValidationStatus = 'idle' | 'validating' | 'valid' | 'invalid';

export function useModelConfig() {
  const [loading, setLoading] = useState(true);
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
  const [configs, setConfigs] = useState<Record<string, PlatformConfig>>({});
  const [validationStatus, setValidationStatus] = useState<ValidationStatus>('idle');
  const [validationMsg, setValidationMsg] = useState('');
  const [saving, setSaving] = useState(false);
  const [discoveredModels, setDiscoveredModels] = useState<DiscoveredModel[]>([]);
  const [discovering, setDiscovering] = useState(false);
  const [batchSaving, setBatchSaving] = useState(false);
  const [providerDiscoveredModels, setProviderDiscoveredModels] = useState<Record<string, DiscoveredModel[]>>({});

  // 加载配置
  const loadConfigs = async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const resp = await settingsApi.getModelConfigs();
      if (resp.success && resp.data) {
        const merged: Record<string, PlatformConfig> = {};
        for (const cfg of resp.data) {
          const provider = cfg.provider;
          if (!merged[provider]) {
            merged[provider] = {
              api_key: cfg.api_key || '',
              api_base: cfg.api_base || '',
              llm_model: '',
              embedding_model: '',
              rerank_model: '',
              image_generation_model: '',
              video_generation_model: '',
            };
          }
          if (cfg.api_key) merged[provider].api_key = cfg.api_key;
          if (cfg.api_base) merged[provider].api_base = cfg.api_base;

          if (cfg.model_type === 'llm') {
            merged[provider].llm_model = cfg.model_name;
            merged[provider].llm_id = cfg.id;
          } else if (cfg.model_type === 'embedding') {
            merged[provider].embedding_model = cfg.model_name;
            merged[provider].embedding_id = cfg.id;
          } else if (cfg.model_type === 'rerank') {
            merged[provider].rerank_model = cfg.model_name;
            merged[provider].rerank_id = cfg.id;
          } else if (cfg.model_type === 'image_generation') {
            merged[provider].image_generation_model = cfg.model_name;
            merged[provider].image_generation_id = cfg.id;
          } else if (cfg.model_type === 'video_generation') {
            merged[provider].video_generation_model = cfg.model_name;
            merged[provider].video_generation_id = cfg.id;
          }
        }
        setConfigs(merged);

        const discoveredFromSaved: Record<string, DiscoveredModel[]> = {};
        for (const cfg of resp.data) {
          const provider = cfg.provider;
          if (!discoveredFromSaved[provider]) discoveredFromSaved[provider] = [];
          discoveredFromSaved[provider].push({
            name: cfg.model_name,
            model_type: cfg.model_type as 'llm' | 'embedding' | 'rerank'
          });
        }
        setProviderDiscoveredModels(prev => ({ ...prev, ...discoveredFromSaved }));

        if (!silent) {
          const firstConfigured = Object.keys(merged)[0];
          if (firstConfigured) setSelectedProvider(firstConfigured);
        }
      }
    } catch {
      message.error('加载模型配置失败');
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    loadConfigs();
  }, []);

  const getConfig = (provider: string): PlatformConfig => {
    return configs[provider] ?? {
      api_key: '',
      api_base: '',
      llm_model: '',
      embedding_model: '',
      rerank_model: '',
      image_generation_model: '',
      video_generation_model: '',
    };
  };

  const updateConfig = (provider: string, patch: Partial<PlatformConfig>) => {
    setConfigs(prev => ({
      ...prev,
      [provider]: { ...getConfig(provider), ...patch },
    }));
  };

  const handleSelectProvider = (provider: string) => {
    setSelectedProvider(prev => prev === provider ? null : provider);
    setValidationStatus('idle');
    setValidationMsg('');
    setDiscoveredModels([]);
  };

  const handleDiscover = async () => {
    if (!selectedProvider) return;
    const cfg = getConfig(selectedProvider);
    setDiscovering(true);
    setDiscoveredModels([]);
    try {
      const resp = await settingsApi.discoverModels(
        selectedProvider,
        cfg.api_key,
        cfg.api_base || undefined
      );
      if (resp.success && resp.data) {
        setDiscoveredModels(resp.data.models);
        if (resp.data.models.length === 0) {
          message.warning('未发现可用模型，请检查 API Key 权限');
        }
      } else {
        message.error('模型发现失败');
      }
    } catch {
      message.error('网络请求失败，请检查连接');
    } finally {
      setDiscovering(false);
    }
  };

  const handleBatchSave = async () => {
    if (!selectedProvider || discoveredModels.length === 0) return;
    const cfg = getConfig(selectedProvider);
    setBatchSaving(true);
    try {
      const items = discoveredModels.map(m => ({
        provider: selectedProvider,
        model_name: m.name,
        model_type: m.model_type,
        api_key: cfg.api_key,
        api_base: cfg.api_base || null,
      }));
      const resp = await settingsApi.batchSaveModels(items);
      if (resp.success) {
        message.success(`已保存 ${discoveredModels.length} 个模型配置`);
        setProviderDiscoveredModels(prev => ({
          ...prev,
          [selectedProvider]: discoveredModels,
        }));
        setDiscoveredModels([]);
        await loadConfigs(true);
      } else {
        message.error('批量保存失败，请重试');
      }
    } catch {
      message.error('批量保存失败，请重试');
    } finally {
      setBatchSaving(false);
    }
  };

  const handleValidate = async () => {
    if (!selectedProvider) return;
    const cfg = getConfig(selectedProvider);

    if (selectedProvider === 'private' && !cfg.api_key.trim()) {
      if (!cfg.api_base?.trim()) {
        message.warning('请先填写 API Base URL');
        return;
      }
      setValidationStatus('valid');
      setValidationMsg('私有部署无需验证');
      return;
    }

    if (!cfg.api_key.trim()) {
      message.warning('请先输入 API Key');
      return;
    }
    setValidationStatus('validating');
    setValidationMsg('');
    try {
      const resp = await settingsApi.validateApiKey(
        selectedProvider,
        cfg.api_key,
        cfg.api_base || undefined
      );
      if (resp.success && resp.data) {
        setValidationStatus(resp.data.valid ? 'valid' : 'invalid');
        setValidationMsg(resp.data.message);
      } else {
        setValidationStatus('invalid');
        setValidationMsg(resp.error?.message || '验证请求失败');
      }
    } catch {
      setValidationStatus('invalid');
      setValidationMsg('网络请求失败，请检查连接');
    }
  };

  return {
    loading,
    selectedProvider,
    configs,
    validationStatus,
    validationMsg,
    saving,
    discoveredModels,
    discovering,
    batchSaving,
    providerDiscoveredModels,
    setSelectedProvider,
    setSaving,
    getConfig,
    updateConfig,
    handleSelectProvider,
    handleDiscover,
    handleBatchSave,
    handleValidate,
    loadConfigs,
  };
}
