import React from 'react';
import { Card, Descriptions, Tag, Typography, Button, Spin, Table, Modal, Form, InputNumber, Select, Switch, message } from 'antd';
import { SettingOutlined, PlusOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { settingsApi } from '@/api';

const { Title } = Typography;
const { Option } = Select;

export function SettingsPage() {
  const [form] = Form.useForm();
  const [modalOpen, setModalOpen] = React.useState(false);
  const qc = useQueryClient();

  const { data: config, isLoading: configLoading } = useQuery({ queryKey: ['config'], queryFn: settingsApi.getConfig });
  const { data: limits, isLoading: limitsLoading } = useQuery({ queryKey: ['cost-limits'], queryFn: settingsApi.getCostLimits });

  const createLimitMutation = useMutation({
    mutationFn: (data: object) => settingsApi.createCostLimit(data),
    onSuccess: () => { message.success('Cost limit created!'); qc.invalidateQueries({ queryKey: ['cost-limits'] }); setModalOpen(false); form.resetFields(); },
  });

  const limitColumns = [
    { title: 'Type', dataIndex: 'limit_type', key: 'type', render: (t: string) => <Tag>{t}</Tag> },
    { title: 'Limit (USD)', dataIndex: 'limit_usd', key: 'limit', render: (v: number) => `$${v}` },
    { title: 'Alert Threshold', dataIndex: 'alert_threshold_pct', key: 'threshold', render: (v: number) => `${v}%` },
    { title: 'Pause on Exceed', dataIndex: 'pause_on_exceed', key: 'pause', render: (v: boolean) => v ? '✅' : '❌' },
    { title: 'Active', dataIndex: 'is_active', key: 'active', render: (v: boolean) => v ? <Tag color="green">Active</Tag> : <Tag>Inactive</Tag> },
  ];

  if (configLoading) return <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>;

  return (
    <div>
      <Title level={3}><SettingOutlined /> System Settings</Title>

      {/* Provider Configuration */}
      <Card title="AI Provider Configuration" style={{ marginBottom: 24 }}>
        <Descriptions column={{ xs: 1, sm: 2, md: 3 }} bordered size="small">
          {[
            ['LLM Provider', config?.llm_provider],
            ['Image Provider', config?.image_provider],
            ['Video Provider', config?.video_provider],
            ['TTS Provider', config?.tts_provider],
            ['Music Provider', config?.music_provider],
            ['Storage Provider', config?.storage_provider],
            ['Daily Video Target', config?.daily_video_target],
            ['Scheduler', config?.scheduler_enabled ? '✅ Enabled' : '❌ Disabled'],
            ['YouTube Connected', config?.youtube_connected ? '✅ Connected' : '❌ Not Connected'],
          ].map(([label, value]) => (
            <Descriptions.Item key={String(label)} label={String(label)}>
              <Tag color={
                String(value).includes('mock') ? 'orange' :
                String(value).includes('✅') ? 'green' :
                String(value).includes('❌') ? 'red' : 'blue'
              }>{String(value)}</Tag>
            </Descriptions.Item>
          ))}
        </Descriptions>
      </Card>

      {/* Cost Limits */}
      <Card
        title="Cost Limits"
        extra={<Button icon={<PlusOutlined />} type="primary" onClick={() => setModalOpen(true)}
          style={{ background: '#ea580c', borderColor: '#ea580c' }}>Add Limit</Button>}
      >
        <Table
          dataSource={limits as any[] || []}
          columns={limitColumns}
          rowKey="id"
          loading={limitsLoading}
          pagination={false}
        />
      </Card>

      <Modal title="Create Cost Limit" open={modalOpen} onCancel={() => { setModalOpen(false); form.resetFields(); }} footer={null}>
        <Form form={form} layout="vertical" onFinish={createLimitMutation.mutate}>
          <Form.Item name="limit_type" label="Limit Type" rules={[{ required: true }]}>
            <Select>
              <Option value="daily">Daily</Option>
              <Option value="monthly">Monthly</Option>
            </Select>
          </Form.Item>
          <Form.Item name="limit_usd" label="Limit (USD)" rules={[{ required: true }]}>
            <InputNumber min={1} style={{ width: '100%' }} prefix="$" />
          </Form.Item>
          <Form.Item name="alert_threshold_pct" label="Alert Threshold %" initialValue={80}>
            <InputNumber min={1} max={100} style={{ width: '100%' }} suffix="%" />
          </Form.Item>
          <Form.Item name="pause_on_exceed" label="Pause Production When Exceeded" valuePropName="checked" initialValue={true}>
            <Switch />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={createLimitMutation.isPending} block
              style={{ background: '#ea580c', borderColor: '#ea580c' }}>
              Create Limit
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
