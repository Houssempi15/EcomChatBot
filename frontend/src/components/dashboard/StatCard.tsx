'use client';

import { Card, Typography } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, MinusOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface StatCardProps {
  title: string;
  value: string | number;
  change?: number;
  suffix?: string;
  prefix?: React.ReactNode;
  accentColor?: string;
}

const defaultAccents = ['#6366F1', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'];
let accentIndex = 0;

export default function StatCard({
  title,
  value,
  change,
  suffix,
  prefix,
  accentColor,
}: StatCardProps) {
  const accent = accentColor || defaultAccents[accentIndex++ % defaultAccents.length];

  const getChangeDisplay = () => {
    if (change === undefined) return null;
    if (change === 0) {
      return { icon: <MinusOutlined />, color: '#6B7280', text: '0% 较昨日' };
    }
    if (change > 0) {
      return { icon: <ArrowUpOutlined />, color: '#10B981', text: `+${change}% 较昨日` };
    }
    return { icon: <ArrowDownOutlined />, color: '#EF4444', text: `${change}% 较昨日` };
  };

  const changeDisplay = getChangeDisplay();

  return (
    <Card
      className="h-full"
      style={{ borderRadius: 12, border: '1px solid #EDE9FE', overflow: 'hidden' }}
      bodyStyle={{ padding: '20px 20px 16px' }}
    >
      {/* Accent bar */}
      <div
        className="absolute top-0 left-0 w-1 h-full rounded-l-xl"
        style={{ background: accent }}
      />

      <div className="pl-1">
        <Text type="secondary" style={{ fontSize: '0.8rem', fontWeight: 500, letterSpacing: '0.02em', textTransform: 'uppercase' }}>
          {title}
        </Text>

        <div className="flex items-center gap-2 mt-2 mb-1">
          {prefix && <span style={{ color: accent, fontSize: '1.1rem' }}>{prefix}</span>}
          <span style={{ fontSize: '1.8rem', fontWeight: 700, color: '#1E1B4B', lineHeight: 1.2 }}>
            {value}
          </span>
        </div>

        {changeDisplay && (
          <div className="flex items-center gap-1 mt-2">
            <span style={{ color: changeDisplay.color, fontSize: '0.78rem', fontWeight: 500 }}>
              {changeDisplay.icon} {changeDisplay.text}
            </span>
          </div>
        )}

        {suffix && (
          <Text type="secondary" style={{ fontSize: '0.75rem', display: 'block', marginTop: 4 }}>
            {suffix}
          </Text>
        )}
      </div>
    </Card>
  );
}
