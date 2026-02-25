'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Form, Input, Button, Checkbox, Card, Typography, message } from 'antd';
import { MailOutlined, LockOutlined } from '@ant-design/icons';
import { useAuthStore } from '@/store';

const { Title, Text } = Typography;

interface LoginFormValues {
  email: string;
  password: string;
  remember: boolean;
}

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading, error, clearError, isAuthenticated } = useAuthStore();
  const [form] = Form.useForm();

  useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, router]);

  useEffect(() => {
    if (error) {
      message.error(error);
      clearError();
    }
  }, [error, clearError]);

  const onFinish = async (values: LoginFormValues) => {
    const success = await login({
      email: values.email,
      password: values.password,
    });

    if (success) {
      message.success('登录成功');
      router.push('/dashboard');
    }
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center py-12 px-4"
      style={{
        background: 'linear-gradient(135deg, #1E1B4B 0%, #312E81 50%, #4F46E5 100%)',
      }}
    >
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div
          className="absolute -top-40 -right-40 w-96 h-96 rounded-full opacity-20"
          style={{ background: 'radial-gradient(circle, #818CF8, transparent)' }}
        />
        <div
          className="absolute -bottom-40 -left-40 w-96 h-96 rounded-full opacity-20"
          style={{ background: 'radial-gradient(circle, #6366F1, transparent)' }}
        />
      </div>

      <Card
        className="w-full max-w-md relative"
        style={{
          borderRadius: 16,
          border: 'none',
          boxShadow: '0 25px 50px rgba(0,0,0,0.3)',
        }}
        bodyStyle={{ padding: '40px 36px' }}
      >
        {/* Logo & Title */}
        <div className="text-center mb-8">
          <div
            className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4"
            style={{ background: 'linear-gradient(135deg, #6366F1, #818CF8)' }}
          >
            <svg viewBox="0 0 24 24" fill="white" className="w-7 h-7">
              <path d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" strokeWidth="1.5" stroke="white" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <Title level={3} style={{ color: '#1E1B4B', marginBottom: 4, fontWeight: 700 }}>
            电商智能客服平台
          </Title>
          <Text type="secondary" style={{ fontSize: '0.9rem' }}>
            SaaS 租户管理系统
          </Text>
        </div>

        <Form
          form={form}
          name="login"
          onFinish={onFinish}
          autoComplete="off"
          layout="vertical"
          initialValues={{ remember: true }}
        >
          <Form.Item
            name="email"
            label="电子邮箱"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '请输入有效的邮箱地址' },
            ]}
          >
            <Input
              prefix={<MailOutlined className="text-gray-400" />}
              placeholder="admin@example.com"
              size="large"
              style={{ borderRadius: 8 }}
            />
          </Form.Item>

          <Form.Item
            name="password"
            label="密码"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined className="text-gray-400" />}
              placeholder="请输入密码"
              size="large"
              style={{ borderRadius: 8 }}
            />
          </Form.Item>

          <Form.Item>
            <div className="flex justify-between items-center">
              <Form.Item name="remember" valuePropName="checked" noStyle>
                <Checkbox>记住我</Checkbox>
              </Form.Item>
              <Link href="#" className="text-sm" style={{ color: '#6366F1' }}>
                忘记密码?
              </Link>
            </div>
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              size="large"
              block
              loading={isLoading}
              style={{
                borderRadius: 8,
                height: 44,
                background: 'linear-gradient(135deg, #6366F1, #4F46E5)',
                border: 'none',
                fontWeight: 600,
              }}
            >
              登录
            </Button>
          </Form.Item>

          <div className="text-center">
            <Text type="secondary" style={{ fontSize: '0.875rem' }}>
              还没有账号?{' '}
              <Link href="/register" style={{ color: '#6366F1', fontWeight: 500 }}>
                立即注册试用
              </Link>
            </Text>
          </div>
        </Form>
      </Card>
    </div>
  );
}
