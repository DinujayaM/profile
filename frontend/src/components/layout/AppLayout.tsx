import React, { useState } from 'react';
import { Layout, Menu, Avatar, Dropdown, Badge, Button, theme } from 'antd';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import {
  DashboardOutlined, BulbOutlined, FileTextOutlined, AppstoreOutlined,
  VideoCameraOutlined, YoutubeOutlined, BarChartOutlined, SettingOutlined,
  UserOutlined, LogoutOutlined, BellOutlined, PlayCircleOutlined,
  CheckCircleOutlined, CalendarOutlined, DollarOutlined, TeamOutlined,
  AuditOutlined, MenuFoldOutlined, MenuUnfoldOutlined, PictureOutlined,
  SoundOutlined, NodeIndexOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '@/store/authStore';
import styles from './AppLayout.module.css';

const { Sider, Header, Content } = Layout;

const menuItems = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: 'Dashboard' },
  { key: '/research', icon: <BulbOutlined />, label: 'AI Research' },
  { key: '/ideas', icon: <NodeIndexOutlined />, label: 'Video Ideas' },
  { key: '/scripts', icon: <FileTextOutlined />, label: 'Script Generator' },
  { key: '/storyboards', icon: <AppstoreOutlined />, label: 'Storyboard Editor' },
  { key: '/characters', icon: <TeamOutlined />, label: 'Character Library' },
  { key: '/audio', icon: <SoundOutlined />, label: 'Audio Library' },
  { key: '/production', icon: <PlayCircleOutlined />, label: 'Video Production' },
  { key: '/preview', icon: <PictureOutlined />, label: 'Video Preview' },
  { key: '/approval', icon: <CheckCircleOutlined />, label: 'Approval Queue' },
  { key: '/youtube', icon: <YoutubeOutlined />, label: 'YouTube Upload' },
  { key: '/calendar', icon: <CalendarOutlined />, label: 'Publishing Calendar' },
  { key: '/analytics', icon: <BarChartOutlined />, label: 'Analytics' },
  { key: '/api-config', icon: <SettingOutlined />, label: 'API Configuration' },
  { key: '/costs', icon: <DollarOutlined />, label: 'Cost Management' },
  { key: '/users', icon: <UserOutlined />, label: 'User Management' },
  { key: '/settings', icon: <SettingOutlined />, label: 'System Settings' },
  { key: '/audit-logs', icon: <AuditOutlined />, label: 'Audit Logs' },
];

export function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();
  const { token } = theme.useToken();

  const userMenuItems = [
    { key: 'profile', icon: <UserOutlined />, label: 'Profile' },
    { key: 'divider', type: 'divider' as const },
    { key: 'logout', icon: <LogoutOutlined />, label: 'Sign Out', danger: true },
  ];

  const handleUserMenu = ({ key }: { key: string }) => {
    if (key === 'logout') {
      logout();
      navigate('/login');
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        width={240}
        style={{ background: token.colorBgContainer, borderRight: `1px solid ${token.colorBorderSecondary}` }}
      >
        <div style={{
          height: 64, display: 'flex', alignItems: 'center', justifyContent: collapsed ? 'center' : 'flex-start',
          padding: collapsed ? 0 : '0 20px', borderBottom: `1px solid ${token.colorBorderSecondary}`
        }}>
          {collapsed ? (
            <span style={{ fontSize: 24 }}>🌟</span>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 24 }}>🌟</span>
              <div>
                <div style={{ fontWeight: 700, fontSize: 14, lineHeight: 1.2, color: token.colorText }}>TinyTales</div>
                <div style={{ fontSize: 10, color: token.colorTextSecondary }}>World Admin</div>
              </div>
            </div>
          )}
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ borderRight: 0, overflowY: 'auto', height: 'calc(100vh - 64px)' }}
        />
      </Sider>

      <Layout>
        <Header style={{
          padding: '0 24px', background: token.colorBgContainer,
          borderBottom: `1px solid ${token.colorBorderSecondary}`,
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          position: 'sticky', top: 0, zIndex: 100,
        }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
          />
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <Badge count={3} size="small">
              <Button type="text" icon={<BellOutlined />} />
            </Badge>
            <Dropdown menu={{ items: userMenuItems, onClick: handleUserMenu }} placement="bottomRight">
              <div style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8 }}>
                <Avatar style={{ backgroundColor: '#f97316' }}>
                  {user?.username?.[0]?.toUpperCase() || 'A'}
                </Avatar>
                {!collapsed && (
                  <span style={{ fontSize: 13 }}>{user?.username || 'Admin'}</span>
                )}
              </div>
            </Dropdown>
          </div>
        </Header>

        <Content style={{ margin: '24px', minHeight: 'calc(100vh - 112px)' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
