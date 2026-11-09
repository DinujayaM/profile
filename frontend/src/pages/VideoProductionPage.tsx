import React, { useState } from 'react';
import {
  Card, Button, Select, Switch, Typography, Table, Tag, Progress,
  Space, Steps, Modal, message, Row, Col, Statistic, Alert,
} from 'antd';
import { PlayCircleOutlined, ReloadOutlined, EyeOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { videosApi, researchApi } from '@/api';
import type { Video, VideoJob } from '@/types';

const { Title, Text } = Typography;
const { Option } = Select;

const JOB_STEPS = [
  'Generating Script', 'Creating Storyboard', 'Generating Images',
  'Animating Scenes', 'Recording Voiceover', 'Composing Music',
  'Rendering Video', 'Creating Thumbnail', 'Quality Check',
];

const STATUS_COLOR: Record<string, string> = {
  queued: 'default', running: 'processing', completed: 'success', failed: 'error', retrying: 'warning',
};

export function VideoProductionPage() {
  const [selectedIdea, setSelectedIdea] = useState<number | null>(null);
  const [format, setFormat] = useState<'landscape' | 'portrait'>('landscape');
  const [madeForKids, setMadeForKids] = useState(true);
  const [viewingVideo, setViewingVideo] = useState<Video | null>(null);
  const [viewingJobs, setViewingJobs] = useState<VideoJob[] | null>(null);
  const qc = useQueryClient();

  const { data: ideas } = useQuery({ queryKey: ['approved-ideas'], queryFn: () => researchApi.listIdeas(1, 100, 'approved') });
  const { data: videos, isLoading } = useQuery({ queryKey: ['videos'], queryFn: () => videosApi.listVideos(1, 50), refetchInterval: 10000 });

  const startMutation = useMutation({
    mutationFn: () => videosApi.startProduction(selectedIdea!, format, madeForKids),
    onSuccess: () => { message.success('Production pipeline started!'); qc.invalidateQueries({ queryKey: ['videos'] }); },
    onError: (err: any) => message.error(err?.response?.data?.detail || 'Failed to start production'),
  });

  const approveMutation = useMutation({
    mutationFn: (id: number) => videosApi.approveVideo(id),
    onSuccess: () => { message.success('Video approved!'); qc.invalidateQueries({ queryKey: ['videos'] }); },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) => videosApi.rejectVideo(id, reason),
    onSuccess: () => { message.success('Video rejected'); qc.invalidateQueries({ queryKey: ['videos'] }); },
  });

  const viewJobs = async (videoId: number) => {
    const jobs = await videosApi.getJobs(videoId);
    setViewingJobs(jobs);
  };

  const videoColumns = [
    { title: 'Title', dataIndex: 'title', key: 'title', ellipsis: true },
    {
      title: 'Status', dataIndex: 'status', key: 'status',
      render: (s: string) => (
        <Tag color={
          s === 'published' ? 'green' : s === 'pending_approval' ? 'orange' :
          s === 'generating' ? 'blue' : s === 'failed' ? 'red' : 'default'
        }>{s.replace('_', ' ')}</Tag>
      ),
    },
    { title: 'Duration', dataIndex: 'duration_seconds', key: 'dur',
      render: (d?: number) => d ? `${Math.round(d / 60)}m ${Math.round(d % 60)}s` : '—' },
    { title: 'Cost', dataIndex: 'total_cost_usd', key: 'cost',
      render: (c?: number) => c ? `$${c.toFixed(2)}` : '—' },
    { title: 'Quality', dataIndex: 'quality_score', key: 'quality',
      render: (q?: number) => q ? <Progress percent={q} size="small" steps={5} /> : '—' },
    {
      title: 'Actions', key: 'actions',
      render: (_: any, v: Video) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={() => { setViewingVideo(v); viewJobs(v.id); }}>View</Button>
          {v.status === 'pending_approval' && (
            <>
              <Button size="small" type="primary" onClick={() => approveMutation.mutate(v.id)}>Approve</Button>
              <Button size="small" danger onClick={() => rejectMutation.mutate({ id: v.id, reason: 'Quality issue' })}>Reject</Button>
            </>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Title level={3}>🎬 Video Production</Title>

      <Card title="Start New Production" style={{ marginBottom: 24 }}>
        <Row gutter={16} align="middle">
          <Col xs={24} md={8}>
            <div style={{ marginBottom: 8 }}><Text strong>Select Approved Idea</Text></div>
            <Select
              style={{ width: '100%' }} placeholder="Choose an approved idea"
              onChange={setSelectedIdea} value={selectedIdea}
            >
              {ideas?.items.map(i => <Option key={i.id} value={i.id}>{i.title}</Option>)}
            </Select>
          </Col>
          <Col xs={12} md={4}>
            <div style={{ marginBottom: 8 }}><Text strong>Format</Text></div>
            <Select value={format} onChange={setFormat} style={{ width: '100%' }}>
              <Option value="landscape">Landscape (16:9)</Option>
              <Option value="portrait">Portrait (9:16)</Option>
            </Select>
          </Col>
          <Col xs={12} md={4}>
            <div style={{ marginBottom: 8 }}><Text strong>Made for Kids</Text></div>
            <Switch checked={madeForKids} onChange={setMadeForKids} checkedChildren="Yes" unCheckedChildren="No" />
          </Col>
          <Col xs={24} md={8}>
            <div style={{ marginBottom: 8 }}>&nbsp;</div>
            <Button
              type="primary" icon={<PlayCircleOutlined />} size="large"
              disabled={!selectedIdea} loading={startMutation.isPending}
              onClick={() => startMutation.mutate()}
              style={{ background: '#ea580c', borderColor: '#ea580c' }}
            >
              Start Production Pipeline
            </Button>
          </Col>
        </Row>
        <Alert
          type="info"
          message="The production pipeline runs: Script → Storyboard → Images → Video Clips → Voice → Music → Render → Thumbnail → QA → Approval"
          style={{ marginTop: 16 }}
          showIcon
        />
      </Card>

      <Card title={`Videos (${videos?.total || 0})`}
        extra={<Button icon={<ReloadOutlined />} onClick={() => qc.invalidateQueries({ queryKey: ['videos'] })} />}>
        <Table
          dataSource={videos?.items || []}
          columns={videoColumns}
          rowKey="id"
          loading={isLoading}
          pagination={{ pageSize: 20 }}
        />
      </Card>

      <Modal
        title={viewingVideo?.title}
        open={!!viewingVideo}
        onCancel={() => { setViewingVideo(null); setViewingJobs(null); }}
        width={800}
        footer={null}
      >
        {viewingVideo && (
          <div>
            {viewingVideo.thumbnail_url && (
              <img src={viewingVideo.thumbnail_url} alt="thumbnail" style={{ width: '100%', borderRadius: 8, marginBottom: 16 }} />
            )}
            {viewingJobs && viewingJobs.length > 0 && (
              <div>
                <Text strong>Production Jobs:</Text>
                <div style={{ marginTop: 8 }}>
                  {viewingJobs.map(job => (
                    <div key={job.id} style={{ marginBottom: 8 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Text>{job.job_type} {job.step ? `(${job.step})` : ''}</Text>
                        <Tag color={
                          job.status === 'completed' ? 'success' : job.status === 'failed' ? 'error' :
                          job.status === 'running' ? 'processing' : 'default'
                        }>{job.status}</Tag>
                      </div>
                      <Progress percent={job.progress_pct} status={job.status === 'failed' ? 'exception' : undefined} size="small" />
                      {job.error_message && <Text type="danger" style={{ fontSize: 12 }}>{job.error_message}</Text>}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}
