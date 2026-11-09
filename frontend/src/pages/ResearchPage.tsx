import React, { useState } from 'react';
import { Button, Card, Form, Select, InputNumber, Input, Typography, Spin, Table, Tag, Space, Modal, message } from 'antd';
import { BulbOutlined, ReloadOutlined, CheckOutlined, CloseOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { researchApi } from '@/api';
import type { VideoIdea } from '@/types';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

const CATEGORY_COLORS: Record<string, string> = {
  nursery_rhyme: 'purple', educational: 'blue', animal_story: 'green',
  bedtime_story: 'cyan', alphabet: 'orange', numbers: 'gold',
  colors: 'pink', shapes: 'volcano', seasons: 'lime', holiday: 'red',
};

export function ResearchPage() {
  const [form] = Form.useForm();
  const [selectedIdea, setSelectedIdea] = useState<VideoIdea | null>(null);
  const qc = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['ideas'],
    queryFn: () => researchApi.listIdeas(1, 50),
  });

  const generateMutation = useMutation({
    mutationFn: (params: { count: number; categories?: string[]; keywords?: string[] }) =>
      researchApi.generateIdeas(params),
    onSuccess: () => {
      message.success('Video ideas generated!');
      qc.invalidateQueries({ queryKey: ['ideas'] });
    },
    onError: (err: any) => message.error(err?.response?.data?.detail || 'Generation failed'),
  });

  const approveMutation = useMutation({
    mutationFn: (id: number) => researchApi.approveIdea(id),
    onSuccess: () => { message.success('Idea approved!'); qc.invalidateQueries({ queryKey: ['ideas'] }); },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) => researchApi.rejectIdea(id, reason),
    onSuccess: () => { message.success('Idea rejected'); qc.invalidateQueries({ queryKey: ['ideas'] }); },
  });

  const columns = [
    { title: 'Title', dataIndex: 'title', key: 'title', ellipsis: true,
      render: (t: string, r: VideoIdea) => <a onClick={() => setSelectedIdea(r)}>{t}</a> },
    { title: 'Category', dataIndex: 'content_category', key: 'category',
      render: (c: string) => <Tag color={CATEGORY_COLORS[c] || 'default'}>{c.replace('_', ' ')}</Tag> },
    { title: 'Age', dataIndex: 'age_category', key: 'age', render: (a: string) => <Tag>{a}</Tag> },
    { title: 'Duration', dataIndex: 'estimated_duration_minutes', key: 'dur', render: (d: number) => `${d} min` },
    { title: 'Est. Cost', dataIndex: 'estimated_cost_usd', key: 'cost', render: (c?: number) => c ? `$${c}` : '—' },
    { title: 'Status', dataIndex: 'status', key: 'status',
      render: (s: string) => <Tag color={s === 'approved' ? 'green' : s === 'rejected' ? 'red' : 'orange'}>{s}</Tag> },
    {
      title: 'Actions', key: 'actions',
      render: (_: any, r: VideoIdea) => r.status === 'pending' ? (
        <Space>
          <Button size="small" type="primary" icon={<CheckOutlined />} onClick={() => approveMutation.mutate(r.id)}>Approve</Button>
          <Button size="small" danger icon={<CloseOutlined />} onClick={() => rejectMutation.mutate({ id: r.id, reason: 'Not suitable' })}>Reject</Button>
        </Space>
      ) : null,
    },
  ];

  return (
    <div>
      <Title level={3}>🔍 AI Research</Title>

      <Card title="Generate Video Ideas" style={{ marginBottom: 24 }}>
        <Form form={form} layout="inline" onFinish={(v) => generateMutation.mutate(v)} style={{ flexWrap: 'wrap', gap: 8 }}>
          <Form.Item name="count" label="Count" initialValue={5}>
            <InputNumber min={1} max={20} />
          </Form.Item>
          <Form.Item name="categories" label="Categories">
            <Select mode="multiple" placeholder="Any category" style={{ minWidth: 200 }} allowClear>
              {['nursery_rhyme','educational','animal_story','bedtime_story','alphabet','numbers','colors','shapes','science','music'].map(c => (
                <Option key={c} value={c}>{c.replace('_', ' ')}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="keywords" label="Keywords">
            <Select mode="tags" placeholder="Add keywords" style={{ minWidth: 200 }} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" icon={<BulbOutlined />} loading={generateMutation.isPending}
              style={{ background: '#ea580c', borderColor: '#ea580c' }}>
              Generate Ideas
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title={`Video Ideas (${data?.total || 0})`}
        extra={<Button icon={<ReloadOutlined />} onClick={() => qc.invalidateQueries({ queryKey: ['ideas'] })} />}>
        <Table
          dataSource={data?.items || []}
          columns={columns}
          rowKey="id"
          loading={isLoading}
          pagination={{ pageSize: 20 }}
        />
      </Card>

      <Modal
        title={selectedIdea?.title}
        open={!!selectedIdea}
        onCancel={() => setSelectedIdea(null)}
        footer={[
          selectedIdea?.status === 'pending' && (
            <Button key="approve" type="primary" onClick={() => { approveMutation.mutate(selectedIdea!.id); setSelectedIdea(null); }}>
              Approve Idea
            </Button>
          ),
          <Button key="close" onClick={() => setSelectedIdea(null)}>Close</Button>,
        ]}
      >
        {selectedIdea && (
          <div>
            <Paragraph><Text strong>Concept:</Text> {selectedIdea.concept}</Paragraph>
            <Paragraph><Text strong>Educational Value:</Text> {selectedIdea.educational_value || '—'}</Paragraph>
            <Paragraph><Text strong>Age:</Text> {selectedIdea.age_category} | <Text strong>Category:</Text> {selectedIdea.content_category}</Paragraph>
            <Paragraph><Text strong>Duration:</Text> {selectedIdea.estimated_duration_minutes} minutes</Paragraph>
            {selectedIdea.keywords && <Paragraph><Text strong>Keywords:</Text> {selectedIdea.keywords.map(k => <Tag key={k}>{k}</Tag>)}</Paragraph>}
          </div>
        )}
      </Modal>
    </div>
  );
}
