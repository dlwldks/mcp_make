
/**
FloodLevelIndicator 컴포넌트
📊 현재 수위(level)와 최대 수위(maxLevel)를 기반으로 수위 상태를 시각적으로 보여주는 카드 UI입니다.
Progress Bar로 수위 시각화
위험도(Risk Level)를 계산하여 뱃지로 표시
수위 변화 추세(Trend: 상승/하강/유지)를 아이콘으로 표시
이전 수치(comparisonLevel)와 비교 분석 기능 포함
Props:
title: 카드 상단 제목
level: 현재 수위 값 (m)
maxLevel: 최대 수위 값
color: 수위에 따른 컬러 테마 ("blue" | "red" | "green")
comparisonLevel: 비교 대상 수위 값 (optional)
trend: 수위 추세 ("rising" | "falling" | "stable")
showComparison: 비교값 표시 여부
*/


"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { TrendingUp, TrendingDown, Minus, AlertTriangle } from "lucide-react"

interface FloodLevelIndicatorProps {
  title: string
  level: number
  maxLevel: number
  color: "blue" | "red" | "green"
  comparisonLevel?: number
  trend?: "rising" | "falling" | "stable"
  showComparison?: boolean
}

export function FloodLevelIndicator({
  title,
  level,
  maxLevel,
  color,
  comparisonLevel,
  trend,
  showComparison = false,
}: FloodLevelIndicatorProps) {
  const percentage = (level / maxLevel) * 100
  const comparisonPercentage = comparisonLevel ? (comparisonLevel / maxLevel) * 100 : 0

  const getColorClass = () => {
    switch (color) {
      case "blue":
        return "text-blue-600"
      case "red":
        return "text-red-600"
      case "green":
        return "text-green-600"
      default:
        return "text-slate-600"
    }
  }

  const getProgressColor = () => {
    switch (color) {
      case "blue":
        return "bg-blue-500"
      case "red":
        return "bg-red-500"
      case "green":
        return "bg-green-500"
      default:
        return "bg-slate-500"
    }
  }

  const getRiskLevel = (levelValue: number) => {
    if (levelValue < 2) return { text: "Low Risk", color: "text-green-600", variant: "secondary" as const }
    if (levelValue < 3) return { text: "Medium Risk", color: "text-orange-600", variant: "default" as const }
    return { text: "High Risk", color: "text-red-600", variant: "destructive" as const }
  }

  const getTrendIcon = () => {
    switch (trend) {
      case "rising":
        return <TrendingUp className="h-4 w-4 text-red-500" />
      case "falling":
        return <TrendingDown className="h-4 w-4 text-green-500" />
      default:
        return <Minus className="h-4 w-4 text-slate-500" />
    }
  }

  const risk = getRiskLevel(level)
  const difference = comparisonLevel ? level - comparisonLevel : 0

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-slate-600 flex items-center justify-between">
          {title}
          {trend && getTrendIcon()}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <span className={`text-3xl font-bold ${getColorClass()}`}>{level.toFixed(1)}m</span>
          <Badge variant={risk.variant}>{risk.text}</Badge>
        </div>

        <div className="space-y-2">
          <div className="relative">
            <Progress value={percentage} className="h-3" />
            {showComparison && comparisonLevel && (
              <div
                className="absolute top-0 h-3 bg-slate-300 opacity-50 rounded-full"
                style={{ width: `${Math.min(comparisonPercentage, 100)}%` }}
              />
            )}
          </div>
          <div className="flex justify-between text-xs text-slate-500">
            <span>0m</span>
            <span>{maxLevel}m</span>
          </div>
        </div>

        {showComparison && comparisonLevel && (
          <div className="bg-slate-50 p-3 rounded-lg space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-600">vs Comparison:</span>
              <span className="font-medium">{comparisonLevel.toFixed(1)}m</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-xs text-slate-500">Difference:</span>
              <span
                className={`text-sm font-medium ${
                  difference > 0 ? "text-red-600" : difference < 0 ? "text-green-600" : "text-slate-600"
                }`}
              >
                {difference > 0 ? "+" : ""}
                {difference.toFixed(1)}m
              </span>
              {Math.abs(difference) > 0.5 && <AlertTriangle className="h-3 w-3 text-orange-500" />}
            </div>
          </div>
        )}

        <div className="text-xs text-slate-600 space-y-1">
          <div>• Normal: 0-2m</div>
          <div>• Elevated: 2-3m</div>
          <div>• Flood Warning: 3m+</div>
        </div>
      </CardContent>
    </Card>
  )
}
