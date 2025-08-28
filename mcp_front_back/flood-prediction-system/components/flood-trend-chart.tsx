

/**
 * 📊 FloodTrendChart 컴포넌트
 *
 * 🌊 이 컴포넌트는 특정 지역의 홍수 수위 변화를 시각화한 차트를 제공합니다.
 * - 최근 14일간의 수위 데이터, 현재 수위, 예측 수위를 함께 표시합니다.
 * - 구간별 경고선 (Caution: 2m / Danger: 3m)을 시각적으로 제공합니다.
 * - 현재 수위(초록), 예측 수위(빨강)는 점으로 강조됩니다.
 * - 사용자에게 직관적인 수위 변화 이해를 돕는 용도로 사용됩니다.
 *
 * ✅ 주요 기능:
 * - 14일간의 수위 변화 트렌드 시각화
 * - 현재 수위 및 예측 수위 강조 표시
 * - 수위에 따른 위험 경고선 시각화
 * - 범례(히스토리컬/현재/예측)로 수위 상태 구분
 *
 * 🧩 Props:
 * - `historicalData`: { timestamp: Date; level: number; rainfall?: number }[]
 *   - 14일 수위 데이터 및 선택적 강수량 정보 포함
 * - `currentLevel`: number
 *   - 오늘의 실제 측정 수위
 * - `predictedLevel`: number
 *   - 예측된 내일의 수위
 * - `locationName`: string
 *   - 지역 이름, 카드 상단 제목에 표시됨
 *
 * 📦 의존 라이브러리:
 * - `recharts`: 차트 그리기 (AreaChart, ReferenceLine, Tooltip 등)
 * - `date-fns`: 날짜 포맷팅
 * - UI: Card 컴포넌트 (shadcn/ui)
 *
 * 🔍 내부 처리:
 * - `chartData`: 최근 14일 + 현재 + 예측을 하나의 배열로 구성
 * - `ReferenceLine`: 수위 위험 기준선 시각화
 * - `Line.dot`: 현재/예측 수위를 점으로 표시
 */


"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  AreaChart,
} from "recharts"
import { format } from "date-fns"

interface FloodTrendChartProps {
  historicalData: Array<{ timestamp: Date; level: number; rainfall?: number }>
  currentLevel: number
  predictedLevel: number
  locationName: string
}

export function FloodTrendChart({
  historicalData,
  currentLevel,
  predictedLevel,
  locationName,
}: FloodTrendChartProps) {
  const chartData = [
    ...historicalData.slice(-14).map((data, index) => ({
      date: format(data.timestamp, "MM/dd"),
      level: data.level,
      rainfall: data.rainfall || 0,
      type: "historical",
      day: index - 13,
    })),
    {
      date: "Today",
      level: currentLevel,
      rainfall: 0,
      type: "current",
      day: 0,
    },
    {
      date: "Tomorrow",
      level: predictedLevel,
      rainfall: 0,
      type: "predicted",
      day: 1,
    },
  ]

  const maxLevel = Math.max(...chartData.map((d) => d.level)) + 1

  return (
    <Card>
      <CardHeader>
        <CardTitle>14-Day Flood Level Trend</CardTitle>
        <p className="text-sm text-slate-600">{locationName}</p>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorLevel" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} interval="preserveStartEnd" />
              <YAxis tick={{ fontSize: 12 }} domain={[0, maxLevel]} />
              <Tooltip
                formatter={(value: number, name: string) => [
                  `${value.toFixed(1)}m`,
                  name === "level" ? "Flood Level" : "Rainfall",
                ]}
                labelStyle={{ color: "#374151" }}
              />
              <ReferenceLine y={2} stroke="#f59e0b" strokeDasharray="5 5" label="Caution" />
              <ReferenceLine y={3} stroke="#ef4444" strokeDasharray="5 5" label="Danger" />

              <Area
                type="monotone"
                dataKey="level"
                stroke="#3b82f6"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorLevel)"
              />

              {/* 현재/예측 수위 강조 점 */}
              <Line
              type="monotone"
              dataKey="level"
              stroke="transparent"
              strokeWidth={0}
              dot={(props) => {
                const { cx, cy, payload } = props;

                if (payload.type === "current") {
                  return <circle cx={cx} cy={cy} r={4} fill="#10b981" stroke="#fff" strokeWidth={2} />;
                }

                if (payload.type === "predicted") {
                  return <circle cx={cx} cy={cy} r={4} fill="#ef4444" stroke="#fff" strokeWidth={2} />;
        }

                // 🚫 null 대신 시각적으로 보이지 않는 circle 반환
                return <circle cx={cx} cy={cy} r={0} fill="transparent" />;
        }}
            />

            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* 범례 */}
        <div className="flex items-center justify-center space-x-6 mt-4 text-sm">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <span>Historical</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span>Current</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
            <span>Predicted</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
