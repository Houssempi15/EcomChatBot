'use client';

import { usePathname, useRouter } from 'next/navigation';
import { Menu, Avatar, Typography, Button, Tooltip } from 'antd';
import type { MenuProps } from 'antd';
import {
  DashboardOutlined,
  TeamOutlined,
  CreditCardOutlined,
  DollarOutlined,
  BarChartOutlined,
  AuditOutlined,
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { useAdminStore } from '@/store';

const { Text } = Typography;

type MenuItem = Required<MenuProps>['items'][number];

const menuItems: MenuItem[] = [
  {
    key: '/platform',
    icon: <DashboardOutlined />,
    label: '平台概览',
  },
  {
    key: '/tenants',
    icon: <TeamOutlined />,
    label: '租户管理',
    children: [
      { key: '/tenants', label: '租户列表' },
      { key: '/tenants/overdue', label: '欠费租户' },
    ],
  },
  {
    key: '/subscriptions',
    icon: <CreditCardOutlined />,
    label: '订阅管理',
  },
  {
    key: '/payments',
    icon: <DollarOutlined />,
    label: '支付管理',
    children: [
      { key: '/payments', label: '支付订单' },
      { key: '/payments/bills', label: '账单管理' },
    ],
  },
  {
    key: '/statistics',
    icon: <BarChartOutlined />,
    label: '数据统计',
    children: [
      { key: '/statistics', label: '统计概览' },
      { key: '/statistics/revenue', label: '收入统计' },
      { key: '/statistics/usage', label: '用量分析' },
    ],
  },
  {
    key: '/audit',
    icon: <AuditOutlined />,
    label: '审计监控',
    children: [
      { key: '/audit', label: '操作日志' },
      { key: '/audit/security', label: '安全审计' },
    ],
  },
  {
    key: '/admins',
    icon: <UserOutlined />,
    label: '管理员管理',
  },
];

const roleLabels: Record<string, string> = {
  super_admin: '超级管理员',
  operation_admin: '运营管理员',
  support_admin: '客服管理员',
  readonly_admin: '只读管理员',
};

export default function AdminSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { logout, admin } = useAdminStore();

  const handleMenuClick: MenuProps['onClick'] = ({ key }) => {
    router.push(key);
  };

  const handleLogout = () => {
    logout();
    router.push('/admin-login');
  };

  // Get selected keys based on current pathname
  const getSelectedKeys = () => {
    // For nested routes, match the parent path
    if (pathname.startsWith('/tenants/overdue')) return ['/tenants/overdue'];
    if (pathname.startsWith('/tenants/')) return ['/tenants'];
    if (pathname.startsWith('/payments/bills')) return ['/payments/bills'];
    if (pathname.startsWith('/statistics/revenue')) return ['/statistics/revenue'];
    if (pathname.startsWith('/statistics/usage')) return ['/statistics/usage'];
    if (pathname.startsWith('/audit/security')) return ['/audit/security'];
    return [pathname];
  };

  // Get open keys for submenu
  const getOpenKeys = () => {
    if (pathname.startsWith('/tenants')) return ['/tenants'];
    if (pathname.startsWith('/payments')) return ['/payments'];
    if (pathname.startsWith('/statistics')) return ['/statistics'];
    if (pathname.startsWith('/audit')) return ['/audit'];
    return [];
  };

  return (
    <aside
      className="fixed left-0 top-0 h-screen w-[200px] z-50"
      style={{ background: '#001529' }}
    >
      <div className="flex flex-col h-full">
        {/* Logo */}
        <div className="h-16 flex items-center px-6 border-b border-gray-700">
          <SettingOutlined className="text-2xl text-blue-400 mr-3" />
          <Text strong style={{ color: '#fff', fontSize: '1.05rem' }}>
            平台管理
          </Text>
        </div>

        {/* Menu */}
        <div className="flex-1 py-4 overflow-y-auto">
          <Menu
            mode="inline"
            selectedKeys={getSelectedKeys()}
            defaultOpenKeys={getOpenKeys()}
            onClick={handleMenuClick}
            items={menuItems}
            theme="dark"
            style={{ background: 'transparent', borderRight: 'none' }}
          />
        </div>

        {/* Admin Profile */}
        <div className="p-3">
          <div
            className="flex items-center gap-2.5 px-3 py-2.5 rounded-xl"
            style={{ background: 'rgba(255,255,255,0.07)', border: '1px solid rgba(255,255,255,0.1)' }}
          >
            <Avatar
              size={36}
              style={{ background: '#1677ff', flexShrink: 0, fontWeight: 700, fontSize: '0.9rem' }}
            >
              {admin?.username ? admin.username[0].toUpperCase() : <UserOutlined />}
            </Avatar>
            <div className="flex-1 min-w-0">
              <Text
                className="text-white block truncate"
                style={{ fontSize: '0.82rem', fontWeight: 600, lineHeight: '1.35', letterSpacing: '-0.01em' }}
              >
                {admin?.username || '管理员'}
              </Text>
              <Text
                className="block truncate"
                style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.7rem', lineHeight: '1.35' }}
              >
                {admin?.role ? roleLabels[admin.role] || admin.role : ''}
              </Text>
            </div>
            <Tooltip title="退出登录">
              <Button
                type="text"
                size="small"
                icon={<LogoutOutlined style={{ color: 'rgba(255,255,255,0.5)' }} />}
                onClick={handleLogout}
                className="hover:!bg-white/10 transition-colors flex-shrink-0"
              />
            </Tooltip>
          </div>
        </div>
      </div>
    </aside>
  );
}
