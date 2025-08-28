

/**
 * FloodComparisonChart 컴포넌트
 *
 * - 특정 위치(locationName)의 현재 수위(currentLevel)와 예측 수위(predictedLevel)를 비교하여 시각화합니다.
 * - 수위의 상승, 하락, 안정 여부에 따라 배지를 달리 표시합니다.
 * - 예측과 현재 수위 차이값과 백분율 변화를 함께 제공합니다.
 * - 수위 변화는 시각적으로 bar chart로 렌더링되며, 기준선(주의 2m, 위험 3m)을 함께 표시합니다.
 *
 * props:
 * - currentLevel: 현재 홍수 수위 (단위: meter)
 * - predictedLevel: 24시간 이내 예측 수위 (단위: meter)
 * - locationName: 해당 수위 정보의 위치 이름
 * - historicalData (optional): 과거 수위 데이터 (현재는 미사용)
 */



"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts"

interface FloodComparisonChartProps {
  currentLevel: number
  predictedLevel: number
  locationName: string
  historicalData?: Array<{ timestamp: Date; level: number }>
}

export function FloodComparisonChart({
  currentLevel,
  predictedLevel,
  locationName,
  historicalData = [],
}: FloodComparisonChartProps) {
  const comparisonData = [
    {
      name: "Current",
      level: currentLevel,
      fill: "#3b82f6",
    },
    {
      name: "Predicted (24h)",
      level: predictedLevel,
      fill: "#ef4444",
    },
  ]

  const difference = predictedLevel - currentLevel
  const percentageChange = currentLevel > 0 ? (difference / currentLevel) * 100 : 0

  const getChangeColor = () => {
    if (difference > 0.5) return "text-red-600"
    if (difference < -0.5) return "text-green-600"
    return "text-slate-600"
  }

  const getChangeBadge = () => {
    if (difference > 0.5) return { variant: "destructive" as const, text: "Rising" }
    if (difference < -0.5) return { variant: "secondary" as const, text: "Falling" }
    return { variant: "outline" as const, text: "Stable" }
  }

  const changeBadge = getChangeBadge()

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Current vs Predicted</span>
          <Badge variant={changeBadge.variant}>{changeBadge.text}</Badge>
        </CardTitle>
        <p className="text-sm text-slate-600">{locationName}</p>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Summary Stats */}
          <div className="grid grid-cols-2 gap-4 p-4 bg-slate-50 rounded-lg">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{currentLevel.toFixed(1)}m</div>
              <div className="text-sm text-slate-600">Current Level</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{predictedLevel.toFixed(1)}m</div>
              <div className="text-sm text-slate-600">Predicted Level</div>
            </div>
          </div>

          {/* Change Indicator */}
          <div className="text-center p-3 border rounded-lg">
            <div className={`text-lg font-semibold ${getChangeColor()}`}>
              {difference > 0 ? "+" : ""}
              {difference.toFixed(1)}m
            </div>
            <div className="text-sm text-slate-600">
              Expected Change ({percentageChange > 0 ? "+" : ""}
              {percentageChange.toFixed(1)}%)
            </div>
          </div>

          {/* Bar Chart */}
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={comparisonData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip
                  formatter={(value: number) => [`${value.toFixed(1)}m`, "Flood Level"]}
                  labelStyle={{ color: "#374151" }}
                />
                <ReferenceLine y={2} stroke="#f59e0b" strokeDasharray="5 5" label="Caution Level" />
                <ReferenceLine y={3} stroke="#ef4444" strokeDasharray="5 5" label="Danger Level" />
                <Bar dataKey="level" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
