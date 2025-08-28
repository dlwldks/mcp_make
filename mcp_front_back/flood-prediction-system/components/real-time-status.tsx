
/**
 * 📡 RealTimeStatus 컴포넌트
 *
 * ✅ 이 컴포넌트는 실시간 시스템 상태를 보여주는 카드 UI를 제공합니다.
 * - 연결 상태, 시스템 건강도, 자동 새로고침 제어 등을 시각적으로 표현합니다.
 * - 데이터 지연 시간, 센서 연결 수, 마지막 업데이트 시간 등도 함께 표시됩니다.
 *
 * 🧩 주요 기능:
 * - 연결 상태: 온라인 / 오프라인 / 연결 중 (🌐 `connectionStatus`)
 * - 시스템 건강도 표시: Healthy / Warning / Error (🩺 `systemHealth`)
 * - 자동 새로고침 스위치 토글 (🕒 `Auto Refresh`)
 * - 지연 시간 및 센서 수 실시간 표시
 * - 외부 데이터 소스 상태 표기 (☁️ Weather API, 🛰️ Satellite, 🧱 Ground Sensors)
 *
 * 🔧 Props:
 * - `isAutoRefreshEnabled`: 자동 새로고침 여부 (boolean)
 * - `onAutoRefreshToggle`: 자동 새로고침 토글 시 실행될 함수
 * - `lastUpdated`: 마지막 데이터 갱신 시각 (Date 객체)
 * - `systemHealth`: 시스템 상태 ('healthy' | 'warning' | 'error')
 *
 * 📦 내부 상태:
 * - `connectionStatus`: 현재 연결 상태 (connected / connecting / disconnected)
 * - `dataLatency`: 데이터 수신 지연(ms)
 * - `activeConnections`: 활성화된 센서 개수
 *
 * 💬 기타:
 * - 5초마다 무작위로 상태 업데이트 시뮬레이션
 * - 연결 상태/시스템 건강도에 따라 아이콘 및 배지 색상 동적으로 변경
 */



"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { Wifi, WifiOff, Clock, AlertCircle, CheckCircle, Activity, Database, Satellite } from "lucide-react"

interface RealTimeStatusProps {
  isAutoRefreshEnabled: boolean
  onAutoRefreshToggle: (enabled: boolean) => void
  lastUpdated: Date
  systemHealth: "healthy" | "warning" | "error"
}

export function RealTimeStatus({
  isAutoRefreshEnabled,
  onAutoRefreshToggle,
  lastUpdated,
  systemHealth,
}: RealTimeStatusProps) {
  const [connectionStatus, setConnectionStatus] = useState<"connected" | "disconnected" | "connecting">("connected")
  const [dataLatency, setDataLatency] = useState(120) // ms
  const [activeConnections, setActiveConnections] = useState(8)

  useEffect(() => {
    // Simulate connection status changes
    const interval = setInterval(() => {
      if (Math.random() > 0.95) {
        setConnectionStatus("connecting")
        setTimeout(() => setConnectionStatus("connected"), 2000)
      }

      // Simulate latency variations
      setDataLatency(100 + Math.random() * 50)
      setActiveConnections(6 + Math.floor(Math.random() * 4))
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  const getStatusIcon = () => {
    switch (connectionStatus) {
      case "connected":
        return <Wifi className="h-4 w-4 text-green-500" />
      case "connecting":
        return <Activity className="h-4 w-4 text-yellow-500 animate-pulse" />
      case "disconnected":
        return <WifiOff className="h-4 w-4 text-red-500" />
    }
  }

  const getStatusBadge = () => {
    switch (connectionStatus) {
      case "connected":
        return (
          <Badge variant="secondary" className="text-green-700 bg-green-100">
            Online
          </Badge>
        )
      case "connecting":
        return (
          <Badge variant="default" className="text-yellow-700 bg-yellow-100">
            Connecting
          </Badge>
        )
      case "disconnected":
        return <Badge variant="destructive">Offline</Badge>
    }
  }

  const getHealthIcon = () => {
    switch (systemHealth) {
      case "healthy":
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case "warning":
        return <AlertCircle className="h-4 w-4 text-yellow-500" />
      case "error":
        return <AlertCircle className="h-4 w-4 text-red-500" />
    }
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center space-x-2">
          <Activity className="h-4 w-4" />
          <span>System Status</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Connection Status */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {getStatusIcon()}
            <span className="text-sm font-medium">Connection</span>
          </div>
          {getStatusBadge()}
        </div>

        {/* System Health */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {getHealthIcon()}
            <span className="text-sm font-medium">System Health</span>
          </div>
          <Badge
            variant={systemHealth === "healthy" ? "secondary" : systemHealth === "warning" ? "default" : "destructive"}
          >
            {systemHealth.charAt(0).toUpperCase() + systemHealth.slice(1)}
          </Badge>
        </div>

        {/* Auto Refresh Toggle */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Clock className="h-4 w-4 text-slate-500" />
            <span className="text-sm font-medium">Auto Refresh</span>
          </div>
          <Switch checked={isAutoRefreshEnabled} onCheckedChange={onAutoRefreshToggle} />
        </div>

        {/* Performance Metrics */}
        <div className="pt-2 border-t space-y-2">
          <div className="flex justify-between text-xs">
            <span className="text-slate-600">Data Latency:</span>
            <span className="font-medium">{dataLatency.toFixed(0)}ms</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-slate-600">Active Sensors:</span>
            <span className="font-medium">{activeConnections}/12</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-slate-600">Last Update:</span>
            <span className="font-medium">{lastUpdated.toLocaleTimeString()}</span>
          </div>
        </div>

        {/* Data Sources */}
        <div className="pt-2 border-t">
          <div className="text-xs font-medium text-slate-600 mb-2">Data Sources</div>
          <div className="space-y-1">
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center space-x-1">
                <Database className="h-3 w-3 text-blue-500" />
                <span>Weather API</span>
              </div>
              <Badge variant="secondary" className="text-xs">
                Active
              </Badge>
            </div>
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center space-x-1">
                <Satellite className="h-3 w-3 text-green-500" />
                <span>Satellite Data</span>
              </div>
              <Badge variant="secondary" className="text-xs">
                Active
              </Badge>
            </div>
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center space-x-1">
                <Activity className="h-3 w-3 text-purple-500" />
                <span>Ground Sensors</span>
              </div>
              <Badge variant="secondary" className="text-xs">
                Active
              </Badge>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
