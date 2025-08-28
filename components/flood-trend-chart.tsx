"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  AreaChart,
  Dot,
} from "recharts"

interface FloodTrendChartProps {
  historicalData: Array<{ timestamp: Date; level: number; rainfall?: number }>
  currentLevel: number
  predictedLevel: number
  locationName: string
}

const formatDate = (date: Date) => {
  const month = String(date.getMonth() + 1).padStart(2, "0")
  const day = String(date.getDate()).padStart(2, "0")
  return `${month}/${day}`
}

export function FloodTrendChart({ historicalData, currentLevel, predictedLevel, locationName }: FloodTrendChartProps) {
  const chartData = [
    ...historicalData.slice(-14).map((data, index) => ({
      date: formatDate(data.timestamp), // Using native formatDate function
      level: data.level,
      type: "historical",
      day: index - 13,
    })),
    {
      date: formatDate(new Date()), // Using native formatDate function
      level: currentLevel,
      type: "current",
      day: 0,
    },
    {
      date: "Tomorrow",
      level: predictedLevel,
      type: "predicted",
      day: 1,
    },
  ]

  const CustomDot = (props: any) => {
    const { cx, cy, payload } = props
    if (!payload || !payload.type) {
      return null
    }
    if (payload.type === "current") {
      return <Dot cx={cx} cy={cy} r={4} fill="#10b981" stroke="#fff" strokeWidth={2} />
    }
    if (payload.type === "predicted") {
      return <Dot cx={cx} cy={cy} r={4} fill="#ef4444" stroke="#fff" strokeWidth={2} />
    }
    return null
  }

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-semibold">14-Day Flood Level Trend</CardTitle>
        <p className="text-sm text-gray-500 mt-1">{locationName}</p>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-4">
          {/* Chart - Updated styling to match reference */}
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 10, bottom: 20 }}>
                <defs>
                  <linearGradient id="colorLevel" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="1 1" stroke="#e5e7eb" />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#6b7280" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: "#6b7280" }} axisLine={false} tickLine={false} domain={[0, 3]} />
                <Tooltip
                  formatter={(value: number) => [`${value.toFixed(1)}m`, "Flood Level"]}
                  labelStyle={{ color: "#374151", fontSize: "12px" }}
                  contentStyle={{ fontSize: "12px" }}
                />
                <ReferenceLine
                  y={2.85}
                  stroke="#ef4444"
                  strokeDasharray="3 3"
                  label={{ value: "Danger", position: "right", fontSize: 10, fill: "#6b7280" }}
                />
                <ReferenceLine
                  y={1.9}
                  stroke="#f59e0b"
                  strokeDasharray="3 3"
                  label={{ value: "Caution", position: "right", fontSize: 10, fill: "#6b7280" }}
                />

                <Area
                  type="monotone"
                  dataKey="level"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorLevel)"
                  dot={<CustomDot />}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Legend - Updated to match reference design */}
          <div className="flex items-center justify-center space-x-6 text-xs">
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span className="text-gray-600">Historical</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-gray-600">Current</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-red-500 rounded-full"></div>
              <span className="text-gray-600">Predicted</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
