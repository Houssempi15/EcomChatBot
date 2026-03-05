'use client';

import { ConfigProvider, App } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { ReactNode } from 'react';

const theme = {
  token: {
    colorPrimary: '#6366F1',      // 修复：从 #2563eb 改为 #6366F1（与 CSS 变量一致）
    colorSuccess: '#10B981',
    colorWarning: '#F59E0B',
    colorError: '#EF4444',
    colorInfo: '#3B82F6',
    borderRadius: 6,
    borderRadiusLG: 12,
    colorBgContainer: '#ffffff',
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif',
  },
};

interface AntdConfigProviderProps {
  children: ReactNode;
}

export default function AntdConfigProvider({ children }: AntdConfigProviderProps) {
  return (
    <ConfigProvider locale={zhCN} theme={theme}>
      <App>{children}</App>
    </ConfigProvider>
  );
}
