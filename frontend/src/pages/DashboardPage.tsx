import React from 'react';
import { Row, Col, Card, Statistic, Typography, Table, Tag, Progress, Spin, Alert } from 'antd';
import {
  VideoCameraOutlined, CheckCircleOutlined, ClockCircleOutlined,
  CloseCircleOutlined, YoutubeOutlined, DollarOutlined,
  EyeOutlined, TeamOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { analyticsApi } from '@/api';

const { Title, Text } = Typography;

const STATUS_COLORS: Record<string, string> = {
  draft: '#d9d9d9', generating: '#1677ff', quality_check: '#722ed1',
  pending_approval: '#fa8c16', approved: '#52c41a', rejected: '#ff4d4f',
  uploading: '#13c2c2', published: '#389e0d', failed: '#cf1322', archived: '#8c8c8c',
};

export function DashboardPage() {
  const { data: stats, isLoading: statsLoading, error: statsError } =
    useQuery({ queryKey: ['dashboard-stats'], queryFn: analyticsApi.getDashboardStats, refetchInterval: 30000 });
  const { data: breakdown } =
    useQuery({ queryKey: ['status-breakdown'], queryFn: analyticsApi.getStatusBreakdown });
  const { data: recentVideos } =
    useQuery({ queryKey: ['recent-videos'], queryFn: analyticsApi.getRecentVideos });
  const { data: costData } =
    useQuery({ queryKey: ['cost-breakdown'], queryFn: analyticsApi.getCostByCategory });

  if (statsLoading) return <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>;
  if (statsError) return <Alert type="error" message="Failed to load dashboard data" />;

  const pieData = breakdown?.map(b => ({ name: b.status, value: b.count, color: STATUS_COLORS[b.status] || '#999' })) || [];

  const videoColumns = [
    { title: 'Title', dataIndex: 'title', key: 'title', ellipsis: true },
    {
      title: 'Status', dataIndex: 'status', key: 'status',
      render: (s: string) => <Tag color={STATUS_COLORS[s]}>{s.replace('_', ' ').toUpperCase()}</Tag>
    },
    {
      title: 'Cost', dataIndex: 'total_cost_usd', key: 'cost',
      render: (v: number) => v ? `$${v.toFixed(2)}` : '-'
    },
  ];

  return (
    <div>
      <Title level={3} style={{ marginBottom: 24 }}>📊 Dashboard</Title>

      {/* KPI Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {[
          { title: 'Total Videos', value: stats?.total_videos, icon: <VideoCameraOutlined />, color: '#1677ff' },
          { title: 'Pending Approval', value: stats?.pending_approval, icon: <ClockCircleOutlined />, color: '#fa8c16' },
          { title: 'Published', value: stats?.published_videos, icon: <CheckCircleOutlined />, color: '#52c41a' },
          { title: 'Failed Jobs', value: stats?.failed_jobs, icon: <CloseCircleOutlined />, color: '#ff4d4f' },
          { title: 'YT Views', value: stats?.total_youtube_views?.toLocaleString() ?? '—', icon: <YoutubeOutlined />, color: '#ff0000' },
          { title: 'Subscribers', value: stats?.subscriber_count?.toLocaleString() ?? '—', icon: <TeamOutlined />, color: '#722ed1' },
          { title: 'Daily Cost', value: `$${stats?.daily_cost_usd.toFixed(2)}`, icon: <DollarOutlined />, color: '#13c2c2' },
          { title: 'Monthly Cost', value: `$${stats?.monthly_cost_usd.toFixed(2)}`, icon: <DollarOutlined />, color: '#eb2f96' },
        ].map(card => (
          <Col xs={12} sm={8} lg={6} key={card.title}>
            <Card size="small" style={{ borderTop: `3px solid ${card.color}` }}>
              <Statistic
                title={card.title}
                value={card.value as any}
                prefix={React.cloneElement(card.icon, { style: { color: card.color } })}
                valueStyle={{ fontSize: 20 }}
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[16, 16]}>
        {/* Video Status Breakdown */}
        <Col xs={24} md={10}>
          <Card title="Video Status Breakdown" style={{ height: 320 }}>
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={240}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                    {pieData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>No videos yet</div>
            )}
          </Card>
        </Col>

        {/* Cost Breakdown */}
        <Col xs={24} md={14}>
          <Card title="Cost by Category" style={{ height: 320 }}>
            {costData?.length ? (
              <div style={{ overflowY: 'auto', maxHeight: 240 }}>
                {costData.map(c => (
                  <div key={c.category} style={{ marginBottom: 8 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                      <Text>{c.category.replace('_', ' ')}</Text>
                      <Text strong>${c.total_usd.toFixed(2)}</Text>
                    </div>
                    <Progress
                      percent={Math.min(100, (c.total_usd / (stats?.total_cost_usd || 1)) * 100)}
                      showInfo={false} size="small"
                    />
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>No cost data yet</div>
            )}
          </Card>
        </Col>

        {/* Recent Videos */}
        <Col xs={24}>
          <Card title="Recent Videos">
            <Table
              dataSource={recentVideos || []}
              columns={videoColumns}
              rowKey="id"
              size="small"
              pagination={{ pageSize: 5 }}
              locale={{ emptyText: 'No videos generated yet' }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
