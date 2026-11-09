import React from 'react';
import { Card, Row, Col, Statistic, Typography, Spin } from 'antd';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, Legend } from 'recharts';
import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '@/api';

const { Title } = Typography;

const COLORS = ['#f97316', '#3b82f6', '#10b981', '#6366f1', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

export function AnalyticsPage() {
  const { data: stats, isLoading } = useQuery({ queryKey: ['dashboard-stats'], queryFn: analyticsApi.getDashboardStats });
  const { data: breakdown } = useQuery({ queryKey: ['status-breakdown'], queryFn: analyticsApi.getStatusBreakdown });
  const { data: costs } = useQuery({ queryKey: ['cost-breakdown'], queryFn: analyticsApi.getCostByCategory });

  if (isLoading) return <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>;

  const costChartData = costs?.map(c => ({ name: c.category.replace('_', ' '), value: parseFloat(c.total_usd.toFixed(2)) })) || [];

  return (
    <div>
      <Title level={3}>📈 Analytics</Title>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {[
          { title: 'Total Videos', value: stats?.total_videos ?? 0, suffix: '' },
          { title: 'Published', value: stats?.published_videos ?? 0, suffix: '' },
          { title: 'YT Views', value: stats?.total_youtube_views ?? 0, suffix: '' },
          { title: 'Subscribers', value: stats?.subscriber_count ?? 0, suffix: '' },
          { title: 'Total Spend', value: stats?.total_cost_usd ?? 0, prefix: '$', precision: 2 },
          { title: 'Daily Spend', value: stats?.daily_cost_usd ?? 0, prefix: '$', precision: 2 },
          { title: 'Monthly Spend', value: stats?.monthly_cost_usd ?? 0, prefix: '$', precision: 2 },
          { title: 'Pending Approval', value: stats?.pending_approval ?? 0, suffix: '' },
        ].map(s => (
          <Col xs={12} sm={8} md={6} key={s.title}>
            <Card size="small">
              <Statistic title={s.title} value={s.value} prefix={s.prefix} precision={s.precision} suffix={s.suffix} />
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[16, 16]}>
        {/* Video Status Bar */}
        <Col xs={24} md={12}>
          <Card title="Videos by Status">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={breakdown || []} margin={{ top: 5, right: 20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="status" angle={-30} textAnchor="end" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#f97316" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        {/* Cost Pie */}
        <Col xs={24} md={12}>
          <Card title="Cost Distribution">
            {costChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie data={costChartData} cx="50%" cy="50%" outerRadius={90} dataKey="value" label={({ name, value }) => `${name}: $${value}`}>
                    {costChartData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip formatter={(v: number) => `$${v.toFixed(2)}`} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>No cost data yet</div>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
}
