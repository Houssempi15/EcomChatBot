'use client';

import { useEffect, useState, useCallback } from 'react';
import {
  Card, Button, Input, Select, Space, Tag, message,
  Typography, Row, Col, Spin, Empty, List,
} from 'antd';
import {
  VideoCameraOutlined, SendOutlined, ReloadOutlined,
  CheckCircleOutlined, CloseCircleOutlined, LoadingOutlined,
  ClockCircleOutlined, PlayCircleOutlined,
} from '@ant-design/icons';
import { contentApi, type GenerationTask, type GeneratedAsset, type ProductPrompt } from '@/lib/api/content';
import { productApi } from '@/lib/api/product';
import { settingsApi, type ModelConfig } from '@/lib/api/settings';
import type { Product } from '@/types';

const { TextArea } = Input;
const { Title, Text } = Typography;

export default function VideoPage() {
  const [prompt, setPrompt] = useState('');
  const [selectedProduct, setSelectedProduct] = useState<number | undefined>();
  const [selectedPrompt, setSelectedPrompt] = useState<number | undefined>();
  const [selectedModel, setSelectedModel] = useState<number | undefined>();
  const [imageUrl, setImageUrl] = useState('');
  const [generating, setGenerating] = useState(false);

  const [tasks, setTasks] = useState<GenerationTask[]>([]);
  const [assets, setAssets] = useState<GeneratedAsset[]>([]);
  const [prompts, setPrompts] = useState<ProductPrompt[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [videoModels, setVideoModels] = useState<ModelConfig[]>([]);
  const [loading, setLoading] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [tasksResp, assetsResp, productsResp, modelsResp] = await Promise.all([
        contentApi.listTasks({ task_type: 'video', size: 10 }),
        contentApi.listAssets({ asset_type: 'video', size: 20 }),
        productApi.listProducts({ status: 'active', size: 100 }),
        settingsApi.getModelConfigsByType('video_generation'),
      ]);
      if (tasksResp.success && tasksResp.data) setTasks(tasksResp.data.items);
      if (assetsResp.success && assetsResp.data) setAssets(assetsResp.data.items);
      if (productsResp.success && productsResp.data) setProducts(productsResp.data.items);
      if (modelsResp.success && modelsResp.data) setVideoModels(modelsResp.data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  // 选择商品后加载该商品的 video 类型提示词
  useEffect(() => {
    if (selectedProduct) {
      contentApi.listPrompts({ product_id: selectedProduct, prompt_type: 'video', size: 100 })
        .then(resp => {
          if (resp.success && resp.data) setPrompts(resp.data.items);
        })
        .catch(() => {});
    } else {
      setPrompts([]);
      setSelectedPrompt(undefined);
    }
  }, [selectedProduct]);

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      message.warning('请输入生成提示词');
      return;
    }
    setGenerating(true);
    try {
      const resp = await contentApi.createGeneration({
        task_type: 'video',
        prompt: prompt.trim(),
        product_id: selectedProduct,
        prompt_id: selectedPrompt,
        model_config_id: selectedModel,
        params: imageUrl ? { image_url: imageUrl } : undefined,
      });
      if (resp.success) {
        message.success('视频生成任务已创建');
        setPrompt('');
        setImageUrl('');
        loadData();
      } else {
        message.error(resp.error?.message || '创建失败');
      }
    } catch {
      message.error('创建任务失败');
    } finally {
      setGenerating(false);
    }
  };

  const statusConfig: Record<string, { color: string; icon: React.ReactNode; text: string }> = {
    pending: { color: 'default', icon: <ClockCircleOutlined />, text: '等待中' },
    processing: { color: 'processing', icon: <LoadingOutlined />, text: '生成中' },
    completed: { color: 'success', icon: <CheckCircleOutlined />, text: '已完成' },
    failed: { color: 'error', icon: <CloseCircleOutlined />, text: '失败' },
  };

  return (
    <div style={{ padding: 24 }}>
      <Title level={4} style={{ marginBottom: 24 }}>
        <VideoCameraOutlined style={{ marginRight: 8 }} />
        视频生成工作台
      </Title>

      <Row gutter={24}>
        {/* 左侧：输入区 */}
        <Col span={10}>
          <Card title="生成配置">
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <div>
                <Text strong>关联商品（可选）</Text>
                <Select
                  placeholder="选择商品"
                  allowClear
                  style={{ width: '100%', marginTop: 8 }}
                  value={selectedProduct}
                  onChange={(val) => {
                    setSelectedProduct(val);
                    setSelectedPrompt(undefined);
                  }}
                  showSearch
                  optionFilterProp="label"
                  options={products.map(p => ({ value: p.id, label: p.title }))}
                />
              </div>

              <div>
                <Text strong>参考图片URL（可选，图生视频）</Text>
                <Input
                  placeholder="输入图片URL"
                  value={imageUrl}
                  onChange={e => setImageUrl(e.target.value)}
                  style={{ marginTop: 8 }}
                />
              </div>

              <div>
                <Text strong>视频生成模型（可选）</Text>
                <Select
                  placeholder="选择视频生成模型（不选则使用默认）"
                  allowClear
                  style={{ width: '100%', marginTop: 8 }}
                  value={selectedModel}
                  onChange={setSelectedModel}
                  options={videoModels.map(m => ({
                    value: m.id,
                    label: `${m.provider} / ${m.model_name}${m.is_default ? '（默认）' : ''}`,
                  }))}
                />
              </div>

              {selectedProduct && prompts.length > 0 && (
                <div>
                  <Text strong>使用提示词（可选）</Text>
                  <Select
                    placeholder="选择提示词"
                    allowClear
                    style={{ width: '100%', marginTop: 8 }}
                    value={selectedPrompt}
                    onChange={(val) => {
                      setSelectedPrompt(val);
                      if (val) {
                        const p = prompts.find(p => p.id === val);
                        if (p) setPrompt(p.content);
                      }
                    }}
                    options={prompts.map(p => ({ value: p.id, label: p.name }))}
                  />
                </div>
              )}

              <div>
                <Text strong>生成提示词</Text>
                <TextArea
                  rows={6}
                  value={prompt}
                  onChange={e => setPrompt(e.target.value)}
                  placeholder="描述你想要的视频内容、风格、时长等..."
                  style={{ marginTop: 8 }}
                />
              </div>

              <Button
                type="primary"
                icon={<SendOutlined />}
                loading={generating}
                onClick={handleGenerate}
                block
                size="large"
              >
                生成视频
              </Button>
            </Space>
          </Card>

          {/* 最近任务 */}
          <Card title="最近任务" style={{ marginTop: 16 }}>
            <List
              loading={loading}
              dataSource={tasks}
              renderItem={(task) => {
                const sc = statusConfig[task.status] || statusConfig.pending;
                return (
                  <List.Item
                    actions={[
                      task.status === 'failed' && (
                        <Button
                          key="retry"
                          size="small"
                          icon={<ReloadOutlined />}
                          onClick={() => contentApi.retryTask(task.id).then(loadData)}
                        >
                          重试
                        </Button>
                      ),
                    ].filter(Boolean)}
                  >
                    <List.Item.Meta
                      title={
                        <Space>
                          <Tag icon={sc.icon} color={sc.color}>{sc.text}</Tag>
                          <Text ellipsis style={{ maxWidth: 200 }}>{task.prompt}</Text>
                        </Space>
                      }
                      description={`结果: ${task.result_count} 个 | ${new Date(task.created_at).toLocaleString('zh-CN')}`}
                    />
                  </List.Item>
                );
              }}
              locale={{ emptyText: <Empty description="暂无任务" /> }}
            />
          </Card>
        </Col>

        {/* 右侧：结果展示区 */}
        <Col span={14}>
          <Card title="生成结果">
            {loading ? (
              <div style={{ textAlign: 'center', padding: 60 }}>
                <Spin size="large" />
              </div>
            ) : assets.length === 0 ? (
              <Empty description="暂无生成结果" />
            ) : (
              <Row gutter={[16, 16]}>
                {assets.map((asset) => (
                  <Col key={asset.id} span={12}>
                    <Card
                      size="small"
                      hoverable
                      actions={[
                        <Button
                          key="upload"
                          type="link"
                          size="small"
                          disabled={!!asset.platform_url}
                          onClick={async () => {
                            try {
                              const resp = await contentApi.uploadAssetToPlatform({
                                asset_id: asset.id,
                                platform_config_id: 1,
                              });
                              if (resp.success) {
                                message.success('已上传到平台');
                                loadData();
                              }
                            } catch {
                              message.error('上传失败');
                            }
                          }}
                        >
                          {asset.platform_url ? '已上传' : '上传到平台'}
                        </Button>,
                      ]}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <PlayCircleOutlined style={{ fontSize: 32, color: '#1677ff' }} />
                        <div>
                          {asset.file_url ? (
                            <a href={asset.file_url} target="_blank" rel="noreferrer">
                              查看视频
                            </a>
                          ) : (
                            <Text type="secondary">处理中...</Text>
                          )}
                          <br />
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            {new Date(asset.created_at).toLocaleString('zh-CN')}
                          </Text>
                        </div>
                      </div>
                    </Card>
                  </Col>
                ))}
              </Row>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
}
