'use client';

import { Card, Statistic, Typography } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface StatCardProps {
  title: string;
  value: string | number;
  change?: number;
  suffix?: string;
  prefix?: React.ReactNode;
}

export default function StatCard({
  title,
  value,
  change,
  suffix,
  prefix,
}: StatCardProps) {
  const isPositive = change !== undefined && change >= 0;

  return (
    <Card className="h-full">
      <Statistic
        title={<Text type="secondary">{title}</Text>}
        value={value}
        prefix={prefix}
        valueStyle={{ fontSize: '1.75rem', fontWeight: 'bold' }}
      />
      {change !== undefined && (
        <div className="mt-2">
          <Text
            className={isPositive ? 'text-green-600' : 'text-red-600'}
            style={{ fontSize: '0.85rem' }}
          >
            {isPositive ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
            {' '}
            {Math.abs(change)}% 较昨日
          </Text>
        </div>
      )}
      {suffix && (
        <div className="mt-1">
          <Text type="secondary" style={{ fontSize: '0.8rem' }}>
            {suffix}
          </Text>
        </div>
      )}
    </Card>
  );
}
