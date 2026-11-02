import React from 'react';
import { ChartPoint } from '../types';

interface MiniPriceChartProps {
  points: ChartPoint[];
  height?: number;
  showLabels?: boolean;
  unit?: string;
}

export const MiniPriceChart: React.FC<MiniPriceChartProps> = ({
  points,
  height = 140,
  showLabels = true,
  unit = 'G',
}) => {
  if (!points || points.length < 2) {
    return (
      <div
        style={{
          height,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--text-muted)',
          fontSize: '12px',
        }}
      >
        Grafik maʼlumotlari yuklanmoqda...
      </div>
    );
  }

  const values = points.map((p) => p.value);
  const minVal = Math.min(...values);
  const maxVal = Math.max(...values);
  const valRange = maxVal - minVal || 1;

  const width = 360;
  const paddingX = 10;
  const paddingY = 16;
  const chartHeight = height - paddingY * 2;
  const chartWidth = width - paddingX * 2;

  // Generate SVG coordinates
  const coords = points.map((p, idx) => {
    const x = paddingX + (idx / (points.length - 1)) * chartWidth;
    const y = paddingY + chartHeight - ((p.value - minVal) / valRange) * chartHeight;
    return { x, y };
  });

  const pathD = coords.reduce((acc, curr, idx) => {
    return `${acc} ${idx === 0 ? 'M' : 'L'} ${curr.x.toFixed(1)},${curr.y.toFixed(1)}`;
  }, '');

  const areaD = `${pathD} L ${coords[coords.length - 1].x},${height} L ${coords[0].x},${height} Z`;

  const isUp = points[points.length - 1].value >= points[0].value;
  const strokeColor = isUp ? '#10b981' : '#ef4444';
  const gradientId = `chart-grad-${isUp ? 'up' : 'down'}-${Math.random().toString(36).substring(2, 7)}`;

  return (
    <div style={{ position: 'relative', width: '100%', overflow: 'hidden' }}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        style={{ width: '100%', height, display: 'block' }}
        preserveAspectRatio="none"
      >
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={strokeColor} stopOpacity="0.25" />
            <stop offset="100%" stopColor={strokeColor} stopOpacity="0.0" />
          </linearGradient>
        </defs>

        {/* Gradient fill */}
        <path d={areaD} fill={`url(#${gradientId})`} />

        {/* Main Line */}
        <path
          d={pathD}
          fill="none"
          stroke={strokeColor}
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>

      {showLabels && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: '10px',
            color: 'var(--text-muted)',
            fontFamily: 'var(--font-mono)',
            padding: '2px 8px',
          }}
        >
          <span>Min: {minVal.toLocaleString()} {unit}</span>
          <span>Maks: {maxVal.toLocaleString()} {unit}</span>
        </div>
      )}
    </div>
  );
};
