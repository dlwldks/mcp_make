/**
 * FloodDashboard 컴포넌트
 *
 * 📌 이 컴포넌트는 홍수 예측 시스템의 메인 대시보드를 구성합니다.
 * 사용자는 검색창(LocationSearch)을 통해 지역을 선택하고,
 * 선택된 지역의 현재 수위 / 예측 수위 / 경고 등을 실시간으로 시각화하여 확인할 수 있습니다.
 *
 * 주요 기능:
 * - 현재 수위 및 24시간 예측 수위 요약 카드 출력
 * - 실시간 자동 새로고침 (30초 간격)
 * - 시스템 상태(Status: Normal / Monitoring / High Alert) 판단
 * - 홍수 지도(FloodMap)와 차트 시각화 (비교 차트, 추세 차트)
 * - 실시간 알림(AlertPanel) 및 수위 지표(FloodLevelIndicator)
 * - 사용자가 지역을 선택하면 해당 지역의 데이터를 동기화하여 전체 정보 업데이트
 *
 * 내부 상태 관리:
 * - selectedLocation: 현재 선택된 위치의 위도/경도/이름
 * - selectedLocationData: 선택된 위치의 상세 정보 객체
 * - currentFloodLevel / predictedFloodLevel: 현재 및 예측 수위
 * - systemHealth: 시스템 전반 상태 (healthy, warning, error)
 * - isAutoRefreshEnabled: 자동 갱신 활성화 여부
 * - refreshInterval: 데이터 갱신 간격 (기본 30초)
 * - isLoading: 데이터 갱신 중 여부
 *
 * 의존 컴포넌트:
 * - LocationSearch: 검색창
 * - FloodMap: 지도 위 수위 마커
 * - FloodLevelIndicator: 수위 게이지
 * - FloodComparisonChart / FloodTrendChart: 수위 비교 및 추세 시각화
 * - AlertPanel: 알림 요약
 * - RealTimeStatus: 시스템 상태 정보 및 자동 새로고침 제어
 *
 * 💡 추후 확장 포인트:
 * - 실시간 외부 API 연동 (ex. 기상청, 하천청 데이터)
 * - mcp_claude 백엔드에서 수위 예측 결과를 받아와 덮어쓰기
 */

"use client"

import { useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { RefreshCw } from "lucide-react"
import { FloodMap } from "./flood-map"
import { LocationSearch } from "./location-search"
import { FloodLevelIndicator } from "./flood-level-indicator"
import { FloodComparisonChart } from "./flood-comparison-chart"
import { FloodTrendChart } from "./flood-trend-chart"
import { RealTimeStatus } from "./real-time-status"
import { AlertPanel } from "./alert-panel"
import { type FloodLocation } from "@/lib/flood-data-service"

export function FloodDashboard() {
  const [selectedLocation, setSelectedLocation] = useState<{
    lat: number
    lng: number
    name: string
  } | null>(null)

  const [currentFloodLevel, setCurrentFloodLevel] = useState(0)
  const [predictedFloodLevel, setPredictedFloodLevel] = useState(0)
  const [selectedLocationData, setSelectedLocationData] = useState<FloodLocation | null>(null)
  const [lastUpdated, setLastUpdated] = useState(new Date())
  const [isAutoRefreshEnabled, setIsAutoRefreshEnabled] = useState(true)
  const [refreshInterval, setRefreshInterval] = useState(30000)
  const [systemHealth, setSystemHealth] = useState<"healthy" | "warning" | "error">("healthy")
  const [isLoading, setIsLoading] = useState(false)

  const fetchLocationData = async (location: { lat: number; lng: number; name: string }) => {
  try {
    // ✅ 강수량을 먼저 백엔드에서 조회 (별도 API or 내부 계산)
    const rainfallRes = await fetch(`/api/rainfall?lat=${location.lat}&lng=${location.lng}`)
    const rainfallData = await rainfallRes.json()
    const rainfall = rainfallData.rainfall_mm || 0

    // ✅ 침수 예측 요청
    const res = await fetch(
      `/api/flood-info?lat=${location.lat}&lng=${location.lng}&rainfall=${rainfall}&city=${location.name}`
    )
    const data = await res.json()


      const locationData: FloodLocation = {
        id: location.name,
        lat: data.location.lat,
        lng: data.location.lng,
        name: location.name,
        region: "unknown",
        riskLevel: data.flood_data.risk_level,
        currentLevel: data.flood_data.current_level,
        predictedLevel: data.flood_data.predicted_level,
        historicalData: data.trend,
        lastUpdated: new Date(),
      }

      setSelectedLocationData(locationData)
      setCurrentFloodLevel(locationData.currentLevel)
      setPredictedFloodLevel(locationData.predictedLevel)
    } catch (error) {
      console.error("❌ MCP API 연동 오류:", error)
    }
  }

  const handleRefreshData = useCallback(async () => {
    setIsLoading(true)
    try {
      if (selectedLocation) {
        await fetchLocationData(selectedLocation)
        setLastUpdated(new Date())
      }
    } catch (error) {
      setSystemHealth("error")
    } finally {
      setIsLoading(false)
    }
  }, [selectedLocation])

  useEffect(() => {
    if (!isAutoRefreshEnabled) return
    const interval = setInterval(() => {
      handleRefreshData()
    }, refreshInterval)
    return () => clearInterval(interval)
  }, [isAutoRefreshEnabled, refreshInterval, handleRefreshData])

  const handleLocationSelect = async (location: { lat: number; lng: number; name: string }) => {
    setSelectedLocation(location)
    await fetchLocationData(location)
  }

  const handleAutoRefreshToggle = (enabled: boolean) => {
    setIsAutoRefreshEnabled(enabled)
    if (enabled) handleRefreshData()
  }

  const getStatusVariant = () => {
    if (predictedFloodLevel > 3.5) return "destructive"
    if (predictedFloodLevel > 2) return "default"
    return "secondary"
  }

  const overallStatus = () => {
    if (predictedFloodLevel > 3.5) return "High Alert"
    if (predictedFloodLevel > 2) return "Monitoring"
    return "Normal"
  }

  return (
    <div className="container mx-auto p-4 space-y-6">
      <div className="text-center space-y-2">
        <h1 className="text-4xl font-bold text-slate-800">Flood Prediction System</h1>
        <p className="text-slate-600">Real-time flood monitoring and prediction visualization</p>
        <div className="flex items-center justify-center space-x-4 text-sm">
          <Badge variant={getStatusVariant()} className="px-3 py-1">
            System Status: {overallStatus()}
          </Badge>
          <div className="flex items-center space-x-2 text-slate-500">
            <span>Last updated: {lastUpdated.toLocaleTimeString()}</span>
            <Button variant="ghost" size="sm" onClick={handleRefreshData} disabled={isLoading}>
              <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
            </Button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Current Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              <Badge variant={currentFloodLevel > 3 ? "destructive" : "secondary"}>
                {currentFloodLevel > 3 ? "High Risk" : "Normal"}
              </Badge>
              <span className="text-2xl font-bold">{currentFloodLevel.toFixed(1)}m</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">24h Prediction</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              <Badge variant={predictedFloodLevel > 3 ? "destructive" : "default"}>
                {predictedFloodLevel > 3 ? "Flood Warning" : "Elevated"}
              </Badge>
              <span className="text-2xl font-bold">{predictedFloodLevel.toFixed(1)}m</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Selected Location</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg font-medium truncate">
              {selectedLocation ? selectedLocation.name : "No location selected"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Auto Refresh</CardTitle>
          </CardHeader>
          <CardContent>
            <RealTimeStatus
              isAutoRefreshEnabled={isAutoRefreshEnabled}
              onAutoRefreshToggle={handleAutoRefreshToggle}
              lastUpdated={lastUpdated}
              systemHealth={systemHealth}
            />
          </CardContent>
        </Card>
      </div>

      <LocationSearch onLocationSelect={handleLocationSelect} />

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Flood Level Map</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <FloodMap
              selectedLocation={selectedLocation}
              onLocationSelect={handleLocationSelect}
              onFloodLevelChange={(current, predicted) => {
                setCurrentFloodLevel(current)
                setPredictedFloodLevel(predicted)
              }}
            />
          </CardContent>
        </Card>

        <div className="lg:col-span-2 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FloodLevelIndicator
              title="Current Level"
              level={currentFloodLevel}
              maxLevel={6}
              color="blue"
              comparisonLevel={predictedFloodLevel}
              trend={undefined}
              showComparison={true}
            />
            <FloodLevelIndicator
              title="Predicted Level (24h)"
              level={predictedFloodLevel}
              maxLevel={6}
              color="red"
              comparisonLevel={currentFloodLevel}
              showComparison={true}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <AlertPanel onLocationSelect={handleLocationSelect} />
          </div>
        </div>
      </div>

      {selectedLocationData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <FloodComparisonChart
            currentLevel={currentFloodLevel}
            predictedLevel={predictedFloodLevel}
            locationName={selectedLocation?.name || "Unknown Location"}
            historicalData={selectedLocationData.historicalData}
          />
          <FloodTrendChart
            historicalData={selectedLocationData.historicalData}
            currentLevel={currentFloodLevel}
            predictedLevel={predictedFloodLevel}
            locationName={selectedLocation?.name || "Unknown Location"}
          />
        </div>
      )}
    </div>
  )
}
