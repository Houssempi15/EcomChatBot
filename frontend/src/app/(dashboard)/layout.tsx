'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Layout, Spin } from 'antd';
import { Sidebar, Header } from '@/components/layout';
import { useAuthStore } from '@/store';

const { Content } = Layout;

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { isAuthenticated, checkAuth } = useAuthStore();

  useEffect(() => {
    const isAuth = checkAuth();
    if (!isAuth) {
      router.push('/login');
    }
  }, [checkAuth, router]);

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Spin size="large" tip="加载中..." />
      </div>
    );
  }

  return (
    <Layout className="min-h-screen">
      <Sidebar />
      <Layout className="ml-60">
        <Header />
        <Content className="p-6 bg-gray-100">{children}</Content>
      </Layout>
    </Layout>
  );
}
