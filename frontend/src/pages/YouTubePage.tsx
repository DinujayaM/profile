import React, { useState } from 'react';
import { Card, Button, Table, Tag, Typography, Space, Alert, Statistic, Row, Col, Modal, Form, Input, Select, Switch, message } from 'antd';
import { YoutubeOutlined, LinkOutlined, UploadOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { youtubeApi, videosApi } from '@/api';
import type { Video } from '@/types';

const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

export function YouTubePage() {
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null);
  const [form] = Form.useForm();
  const qc = useQueryClient();

  const { data: channels } = useQuery({ queryKey: ['yt-channels'], queryFn: youtubeApi.listChannels });
  const { data: uploads } = useQuery({ queryKey: ['yt-uploads'], queryFn: youtubeApi.listUploads, refetchInterval: 15000 });
  const { data: approvedVideos } = useQuery({ queryKey: ['approved-videos'], queryFn: () => videosApi.listVideos(1, 50, 'approved') });

  const authUrlMutation = useMutation({
    mutationFn: youtubeApi.getAuthUrl,
    onSuccess: (data) => window.open(data.auth_url, '_blank'),
    onError: (err: any) => message.error(err?.response?.data?.detail || 'Failed to get auth URL'),
  });

  const uploadMutation = useMutation({
    mutationFn: (data: object) => youtubeApi.scheduleUpload(data),
    onSuccess: () => {
      message.success('Upload scheduled!');
      qc.invalidateQueries({ queryKey: ['yt-uploads'] });
      setUploadModalOpen(false);
      form.resetFields();
    },
    onError: (err: any) => message.error(err?.response?.data?.detail || 'Upload failed'),
  });

  const uploadColumns = [
    { title: 'Video ID', dataIndex: 'video_id', key: 'vid' },
    { title: 'YouTube ID', dataIndex: 'youtube_video_id', key: 'ytid', render: (id?: string) => id ? <a href={`https://youtu.be/${id}`} target="_blank">{id}</a> : '—' },
    {
      title: 'Status', dataIndex: 'upload_status', key: 'status',
      render: (s: string) => <Tag color={s === 'published' ? 'green' : s === 'failed' ? 'red' : 'blue'}>{s}</Tag>
    },
    { title: 'Progress', dataIndex: 'upload_progress_pct', key: 'prog', render: (p: number) => `${p}%` },
    { title: 'Error', dataIndex: 'error_message', key: 'err', ellipsis: true, render: (e?: string) => e || '—' },
  ];

  return (
    <div>
      <Title level={3}><YoutubeOutlined style={{ color: '#ff0000' }} /> YouTube Integration</Title>

      {/* Channel Status */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {channels?.length ? channels.map(ch => (
          <Col xs={24} md={12} key={ch.id}>
            <Card title={ch.channel_name || 'YouTube Channel'}>
              <Row gutter={16}>
                <Col span={8}><Statistic title="Subscribers" value={ch.subscriber_count?.toLocaleString() ?? '—'} /></Col>
                <Col span={8}><Statistic title="Total Views" value={ch.total_views?.toLocaleString() ?? '—'} /></Col>
                <Col span={8}><Statistic title="Videos" value={ch.video_count ?? '—'} /></Col>
              </Row>
              <div style={{ marginTop: 16 }}>
                <Text>Quota used today: {ch.quota_used_today} / {ch.daily_quota_limit}</Text>
              </div>
            </Card>
          </Col>
        )) : (
          <Col xs={24}>
            <Alert
              type="warning"
              message="No YouTube channel connected"
              description="Connect your YouTube channel to start uploading videos."
              action={
                <Button
                  type="primary" icon={<LinkOutlined />} loading={authUrlMutation.isPending}
                  onClick={() => authUrlMutation.mutate()}
                  style={{ background: '#ff0000', borderColor: '#ff0000' }}
                >
                  Connect YouTube Channel
                </Button>
              }
              showIcon
            />
          </Col>
        )}
      </Row>

      {/* Upload Queue */}
      <Card
        title="Upload Queue"
        extra={
          <Button type="primary" icon={<UploadOutlined />} onClick={() => setUploadModalOpen(true)}
            disabled={!channels?.length || !approvedVideos?.items.length}
            style={{ background: '#ff0000', borderColor: '#ff0000' }}>
            Schedule Upload
          </Button>
        }
      >
        <Table dataSource={uploads as any[] || []} columns={uploadColumns} rowKey="id" pagination={{ pageSize: 10 }} />
      </Card>

      {/* Upload Modal */}
      <Modal title="Schedule YouTube Upload" open={uploadModalOpen}
        onCancel={() => { setUploadModalOpen(false); form.resetFields(); }} footer={null} width={600}>
        <Form form={form} layout="vertical"
          onFinish={(values) => uploadMutation.mutate({ ...values, video_id: selectedVideo?.id })}>
          <Form.Item label="Select Approved Video" required>
            <Select placeholder="Choose video" onChange={(id) => {
              const v = approvedVideos?.items.find(v => v.id === id);
              if (v) { setSelectedVideo(v); form.setFieldValue('title', v.title); }
            }}>
              {approvedVideos?.items.map(v => <Option key={v.id} value={v.id}>{v.title}</Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="title" label="YouTube Title" rules={[{ required: true }]}>
            <Input placeholder="Video title for YouTube" maxLength={100} showCount />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <TextArea rows={4} placeholder="Video description" maxLength={5000} showCount />
          </Form.Item>
          <Form.Item name="privacy_status" label="Privacy" initialValue="private">
            <Select>
              <Option value="private">Private (review before publishing)</Option>
              <Option value="unlisted">Unlisted</Option>
              <Option value="public">Public</Option>
            </Select>
          </Form.Item>
          <Form.Item name="made_for_kids" label="Made for Kids" valuePropName="checked" initialValue={true}>
            <Switch checkedChildren="Yes" unCheckedChildren="No" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={uploadMutation.isPending} block
              style={{ background: '#ff0000', borderColor: '#ff0000' }}>
              Schedule Upload
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
