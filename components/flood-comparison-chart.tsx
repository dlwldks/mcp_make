"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, ReferenceLine } from "recharts"

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

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-semibold">Current vs Predicted</CardTitle>
          <Badge variant="destructive" className="bg-red-500 text-white text-xs px-2 py-1">
            Rising
          </Badge>
        </div>
        <p className="text-sm text-gray-500 mt-1">{locationName}</p>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-6">
          {/* Summary Stats - Updated layout to match reference */}
          <div className="grid grid-cols-2 gap-8">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-500">{currentLevel.toFixed(1)}m</div>
              <div className="text-sm text-gray-500 mt-1">Current Level</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-red-500">{predictedLevel.toFixed(1)}m</div>
              <div className="text-sm text-gray-500 mt-1">Predicted Level</div>
            </div>
          </div>

          {/* Change Indicator - Updated styling */}
          <div className="text-center">
            <div className="text-lg font-semibold text-red-500">+{difference.toFixed(1)}m</div>
            <div className="text-sm text-gray-500">Expected Change (+{percentageChange.toFixed(1)}%)</div>
          </div>

          {/* Bar Chart - Updated to match reference design */}
          <div className="h-32">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={comparisonData} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: "#6b7280" }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: "#6b7280" }} domain={[0, 3]} />
                <ReferenceLine
                  y={2}
                  stroke="#f59e0b"
                  strokeDasharray="3 3"
                  label={{ value: "Caution Level", position: "right", fontSize: 10, fill: "#6b7280" }}
                />
                <Bar dataKey="level" radius={[0, 0, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
