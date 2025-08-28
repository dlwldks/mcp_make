"use client"

import { useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { RefreshCw } from "lucide-react"
import { CurrentConditionsMap } from "./current-conditions-map"
import { ForecastMap } from "./forecast-map"
import { LocationSearch } from "./location-search"
import { FloodLevelIndicator } from "./flood-level-indicator"
import { FloodComparisonChart } from "./flood-comparison-chart"
import { FloodTrendChart } from "./flood-trend-chart"
import { RealTimeStatus } from "./real-time-status"
import { AlertPanel } from "./alert-panel"
import { floodDataService, type FloodLocation } from "@/lib/flood-data-service"

export function FloodDashboard() {
  const [selectedLocation, setSelectedLocation] = useState<{
    lat: number
    lng: number
    name: string
  } | null>(null)

  const [currentFloodLevel, setCurrentFloodLevel] = useState(2.3)
  const [predictedFloodLevel, setPredictedFloodLevel] = useState(4.1)
  const [selectedLocationData, setSelectedLocationData] = useState<FloodLocation | null>(null)
  const [lastUpdated, setLastUpdated] = useState(new Date())
  const [isAutoRefreshEnabled, setIsAutoRefreshEnabled] = useState(true)
  const [refreshInterval, setRefreshInterval] = useState(30000) // 30 seconds
  const [systemHealth, setSystemHealth] = useState<"healthy" | "warning" | "error">("healthy")
  const [isLoading, setIsLoading] = useState(false)
  const [forecastDay, setForecastDay] = useState(0) // 0 = today, 1 = tomorrow, etc.

  const handleRefreshData = useCallback(async () => {
    setIsLoading(true)
    try {
      // Simulate API call delay
      await new Promise((resolve) => setTimeout(resolve, 500))

      floodDataService.updateFloodData()
      setLastUpdated(new Date())

      // Update system health based on data quality
      const highRiskLocations = floodDataService.getHighRiskLocations()
      if (highRiskLocations.length > 3) {
        setSystemHealth("warning")
      } else if (highRiskLocations.length > 5) {
        setSystemHealth("error")
      } else {
        setSystemHealth("healthy")
      }

      // Update selected location data if one is selected
      if (selectedLocation && selectedLocationData) {
        const updatedLocation = floodDataService.getAllLocations().find((loc) => loc.name === selectedLocation.name)
        if (updatedLocation) {
          setSelectedLocationData(updatedLocation)
          setCurrentFloodLevel(updatedLocation.currentLevel)
          setPredictedFloodLevel(updatedLocation.predictedLevel)
        }
      }
    } catch (error) {
      console.error("Failed to refresh data:", error)
      setSystemHealth("error")
    } finally {
      setIsLoading(false)
    }
  }, [selectedLocation, selectedLocationData])

  useEffect(() => {
    if (!isAutoRefreshEnabled) return

    const interval = setInterval(handleRefreshData, refreshInterval)
    return () => clearInterval(interval)
  }, [isAutoRefreshEnabled, refreshInterval, handleRefreshData])

  const handleLocationSelect = (location: { lat: number; lng: number; name: string }) => {
    setSelectedLocation(location)

    // Find the full location data
    const locationData = floodDataService.getAllLocations().find((loc) => loc.name === location.name)

    if (locationData) {
      setSelectedLocationData(locationData)
      setCurrentFloodLevel(locationData.currentLevel)
      setPredictedFloodLevel(locationData.predictedLevel)
    }
  }

  const handleAutoRefreshToggle = (enabled: boolean) => {
    setIsAutoRefreshEnabled(enabled)
    if (enabled) {
      handleRefreshData()
    }
  }

  // Enhanced status calculation with real-time data
  const overallStatus = () => {
    const highRiskCount = floodDataService.getHighRiskLocations().length
    const activeAlerts = floodDataService.getActiveAlerts().length

    if (highRiskCount > 3 || activeAlerts > 2) return "High Alert"
    if (highRiskCount > 1 || activeAlerts > 0) return "Monitoring"
    return "Normal"
  }

  const getStatusVariant = () => {
    const status = overallStatus()
    if (status === "High Alert") return "destructive"
    if (status === "Monitoring") return "default"
    return "secondary"
  }

  return (
    <div className="container mx-auto p-4 space-y-6">
      {/* Header */}
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

      {/* Location Search */}
      <LocationSearch onLocationSelect={handleLocationSelect} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column - Maps */}
        <div className="space-y-4">
          {/* Current Conditions Map */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <span>Current Conditions</span>
                <Badge variant="secondary" className="text-xs">
                  Weather & Flood Status
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <CurrentConditionsMap
                selectedLocation={selectedLocation}
                onLocationSelect={handleLocationSelect}
                onDataChange={(current, predicted) => {
                  setCurrentFloodLevel(current)
                  setPredictedFloodLevel(predicted)
                }}
              />
            </CardContent>
          </Card>

          {/* Flood Forecast Map */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <CardTitle>Flood Forecast</CardTitle>
                  <Badge variant="outline" className="text-xs">
                    Weather & Flood Prediction
                  </Badge>
                </div>
                <Select
                  value={forecastDay.toString()}
                  onValueChange={(value) => setForecastDay(Number.parseInt(value))}
                >
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="0">Today</SelectItem>
                    <SelectItem value="1">Tomorrow</SelectItem>
                    <SelectItem value="2">2 Days</SelectItem>
                    <SelectItem value="3">3 Days</SelectItem>
                    <SelectItem value="4">4 Days</SelectItem>
                    <SelectItem value="5">5 Days</SelectItem>
                    <SelectItem value="6">6 Days</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <ForecastMap
                selectedLocation={selectedLocation}
                onLocationSelect={handleLocationSelect}
                onDataChange={(current, predicted) => {
                  setCurrentFloodLevel(current)
                  setPredictedFloodLevel(predicted)
                }}
                forecastDay={forecastDay}
              />
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Components */}
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Current Level */}
            <FloodLevelIndicator
              title="Current Level"
              level={currentFloodLevel}
              maxLevel={6}
              color="blue"
              comparisonLevel={predictedFloodLevel}
              trend={selectedLocationData ? floodDataService.getFloodTrend(selectedLocationData.id) : undefined}
              showComparison={true}
            />

            {/* Predicted Level (24h) */}
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
            {/* System Status */}
            <RealTimeStatus
              isAutoRefreshEnabled={isAutoRefreshEnabled}
              onAutoRefreshToggle={handleAutoRefreshToggle}
              lastUpdated={lastUpdated}
              systemHealth={systemHealth}
            />

            {/* Active Alerts */}
            <AlertPanel onLocationSelect={handleLocationSelect} />
          </div>

          {/* Selected Location Info */}
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
        </div>
      </div>

      {/* Detailed Charts */}
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
