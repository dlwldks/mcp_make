
/**
 * AlertPanel 컴포넌트
 *
 * - 현재 활성화된 홍수 경보(flood alert)를 보여주는 패널 UI입니다.
 * - 실시간으로 floodDataService에서 경보 데이터를 받아와 표시합니다.
 * - 경보는 severity(emergency, warning, watch)에 따라 스타일이 달라지며, 사용자에 의해 개별적으로 닫을 수 있습니다.
 * - 각 경보에는 위치 보기 버튼이 있어 지도에 해당 위치로 이동할 수 있습니다.
 * - 상단에는 알림 및 사운드 on/off 토글 버튼이 포함되어 있습니다.
 * - props: onLocationSelect — 위치 버튼 클릭 시 해당 위치 정보를 부모 컴포넌트로 전달합니다.
 */



"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { AlertTriangle, Bell, BellOff, X, Clock, MapPin, Volume2, VolumeX } from "lucide-react"
import { floodDataService, type FloodAlert } from "@/lib/flood-data-service"

interface AlertPanelProps {
  onLocationSelect: (location: { lat: number; lng: number; name: string }) => void
}

export function AlertPanel({ onLocationSelect }: AlertPanelProps) {
  const [alerts, setAlerts] = useState<FloodAlert[]>([])
  const [dismissedAlerts, setDismissedAlerts] = useState<Set<string>>(new Set())
  const [soundEnabled, setSoundEnabled] = useState(true)
  const [notificationsEnabled, setNotificationsEnabled] = useState(true)

  useEffect(() => {
    const updateAlerts = () => {
      const activeAlerts = floodDataService.getActiveAlerts()
      setAlerts(activeAlerts)
    }

    updateAlerts()
    const interval = setInterval(updateAlerts, 30000) // Update every 30 seconds

    return () => clearInterval(interval)
  }, [])

  const handleDismissAlert = (alertId: string) => {
    setDismissedAlerts((prev) => new Set([...prev, alertId]))
  }

  const handleGoToLocation = (alert: FloodAlert) => {
    const location = floodDataService.getLocationById(alert.locationId)
    if (location) {
      onLocationSelect({
        lat: location.lat,
        lng: location.lng,
        name: location.name,
      })
    }
  }

  const getAlertIcon = (severity: string) => {
    switch (severity) {
      case "emergency":
        return <AlertTriangle className="h-4 w-4 text-red-600" />
      case "warning":
        return <AlertTriangle className="h-4 w-4 text-orange-600" />
      case "watch":
        return <Clock className="h-4 w-4 text-yellow-600" />
      default:
        return <AlertTriangle className="h-4 w-4 text-slate-600" />
    }
  }

  const getAlertBadgeVariant = (severity: string) => {
    switch (severity) {
      case "emergency":
        return "destructive" as const
      case "warning":
        return "default" as const
      case "watch":
        return "secondary" as const
      default:
        return "outline" as const
    }
  }

  const visibleAlerts = alerts.filter((alert) => !dismissedAlerts.has(alert.id))
  const criticalAlerts = visibleAlerts.filter((alert) => alert.severity === "emergency" || alert.severity === "warning")

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium flex items-center space-x-2">
            <Bell className="h-4 w-4" />
            <span>Active Alerts</span>
            {criticalAlerts.length > 0 && (
              <Badge variant="destructive" className="text-xs">
                {criticalAlerts.length}
              </Badge>
            )}
          </CardTitle>
          <div className="flex items-center space-x-1">
            <Button variant="ghost" size="sm" onClick={() => setSoundEnabled(!soundEnabled)} className="h-6 w-6 p-0">
              {soundEnabled ? <Volume2 className="h-3 w-3" /> : <VolumeX className="h-3 w-3" />}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setNotificationsEnabled(!notificationsEnabled)}
              className="h-6 w-6 p-0"
            >
              {notificationsEnabled ? <Bell className="h-3 w-3" /> : <BellOff className="h-3 w-3" />}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {visibleAlerts.length === 0 ? (
          <div className="text-center py-4 text-slate-500">
            <Bell className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No active alerts</p>
          </div>
        ) : (
          <ScrollArea className="h-64">
            <div className="space-y-3">
              {visibleAlerts.map((alert) => {
                const location = floodDataService.getLocationById(alert.locationId)
                return (
                  <div
                    key={alert.id}
                    className={`p-3 rounded-lg border ${
                      alert.severity === "emergency"
                        ? "bg-red-50 border-red-200"
                        : alert.severity === "warning"
                          ? "bg-orange-50 border-orange-200"
                          : "bg-yellow-50 border-yellow-200"
                    }`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        {getAlertIcon(alert.severity)}
                        <Badge variant={getAlertBadgeVariant(alert.severity)} className="text-xs">
                          {alert.severity.toUpperCase()}
                        </Badge>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDismissAlert(alert.id)}
                        className="h-6 w-6 p-0"
                      >
                        <X className="h-3 w-3" />
                      </Button>
                    </div>

                    <p className="text-sm font-medium mb-1">{alert.message}</p>

                    <div className="flex items-center justify-between text-xs text-slate-600">
                      <div className="flex items-center space-x-1">
                        <MapPin className="h-3 w-3" />
                        <span>{location?.name}</span>
                      </div>
                      <span>{alert.issuedAt.toLocaleTimeString()}</span>
                    </div>

                    <div className="flex items-center space-x-2 mt-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleGoToLocation(alert)}
                        className="text-xs h-6"
                      >
                        View Location
                      </Button>
                      <span className="text-xs text-slate-500">Expires: {alert.expiresAt.toLocaleTimeString()}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  )
}
