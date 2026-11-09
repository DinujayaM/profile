import React from 'react';
import { Card, Typography, Empty } from 'antd';
import { ToolOutlined } from '@ant-design/icons';

interface Props {
  title: string;
  description?: string;
  icon?: string;
}

export function PlaceholderPage({ title, description, icon = '🚧' }: Props) {
  return (
    <div>
      <Typography.Title level={3}>{icon} {title}</Typography.Title>
      <Card>
        <Empty
          description={description || `The ${title} module is included in the production pipeline and will be available once the AI providers are configured.`}
          image={<span style={{ fontSize: 64 }}>{icon}</span>}
        >
          <Typography.Text type="secondary" style={{ display: 'block', textAlign: 'center' }}>
            Configure your AI provider API keys in the Settings → API Configuration section to activate this module.
          </Typography.Text>
        </Empty>
      </Card>
    </div>
  );
}
