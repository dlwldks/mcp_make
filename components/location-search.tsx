"use client"

import { useState, useEffect } from "react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Search, MapPin, AlertTriangle } from "lucide-react"
import { floodDataService, type FloodLocation, getFloodLevelDescription } from "@/lib/flood-data-service"

interface LocationSearchProps {
  onLocationSelect: (location: { lat: number; lng: number; name: string }) => void
}

export function LocationSearch({ onLocationSelect }: LocationSearchProps) {
  const [searchTerm, setSearchTerm] = useState("")
  const [suggestions, setSuggestions] = useState<FloodLocation[]>([])
  const [allLocations, setAllLocations] = useState<FloodLocation[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [showSuggestions, setShowSuggestions] = useState(false)

  useEffect(() => {
    // Load all locations on component mount
    const locations = floodDataService.getAllLocations()
    setAllLocations(locations)
  }, [])

  const handleSearch = (term: string) => {
    setSearchTerm(term)
    setIsLoading(true)

    if (term.length > 0) {
      // Use the flood data service search functionality
      const filtered = floodDataService.searchLocations(term)
      setSuggestions(filtered)
      setShowSuggestions(true)
    } else {
      setSuggestions([])
      setShowSuggestions(false)
    }

    setIsLoading(false)
  }

  const handleLocationSelect = (location: FloodLocation) => {
    onLocationSelect({
      lat: location.lat,
      lng: location.lng,
      name: location.name,
    })
    setSearchTerm(location.name)
    setShowSuggestions(false)
  }

  const handleQuickSelect = (filter: "high-risk" | "all" | "region") => {
    let locations: FloodLocation[] = []

    switch (filter) {
      case "high-risk":
        locations = floodDataService.getHighRiskLocations()
        break
      case "all":
        locations = allLocations
        break
      default:
        locations = allLocations
    }

    setSuggestions(locations)
    setShowSuggestions(true)
    setSearchTerm("")
  }

  const getRiskBadgeVariant = (riskLevel: string) => {
    switch (riskLevel) {
      case "high":
        return "destructive"
      case "medium":
        return "default"
      case "low":
        return "secondary"
      default:
        return "outline"
    }
  }

  const getTrendIcon = (locationId: string) => {
    const trend = floodDataService.getFloodTrend(locationId)
    switch (trend) {
      case "rising":
        return "↗️"
      case "falling":
        return "↘️"
      default:
        return "→"
    }
  }

  return (
    <div className="space-y-4">
      {/* Search Input */}
      <div className="relative">
        <div className="flex space-x-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 h-4 w-4" />
            <Input
              placeholder="Search locations by name or region..."
              value={searchTerm}
              onChange={(e) => handleSearch(e.target.value)}
              onFocus={() => searchTerm.length > 0 && setShowSuggestions(true)}
              className="pl-10"
            />
            {isLoading && (
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                <div className="animate-spin h-4 w-4 border-2 border-slate-300 border-t-slate-600 rounded-full"></div>
              </div>
            )}
          </div>
          <Button
            variant="outline"
            onClick={() => handleQuickSelect("high-risk")}
            className="flex items-center space-x-1"
          >
            <AlertTriangle className="h-4 w-4" />
            <span>High Risk</span>
          </Button>
        </div>

        {/* Search Suggestions */}
        {showSuggestions && suggestions.length > 0 && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-white border rounded-lg shadow-lg z-10 max-h-80 overflow-y-auto">
            {suggestions.map((location) => (
              <button
                key={location.id}
                className="w-full text-left px-4 py-3 hover:bg-slate-50 border-b last:border-b-0 first:rounded-t-lg last:rounded-b-lg transition-colors"
                onClick={() => handleLocationSelect(location)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <MapPin className="h-4 w-4 text-slate-400" />
                      <span className="font-medium">{location.name}</span>
                      <Badge variant="outline" className="text-xs">
                        {location.region}
                      </Badge>
                    </div>
                    <div className="flex items-center space-x-4 text-sm text-slate-600">
                      <span>Current: {location.currentLevel.toFixed(1)}m</span>
                      <span>
                        Predicted: {location.predictedLevel.toFixed(1)}m {getTrendIcon(location.id)}
                      </span>
                    </div>
                  </div>
                  <div className="flex flex-col items-end space-y-1">
                    <Badge variant={getRiskBadgeVariant(location.riskLevel)} className="text-xs">
                      {location.riskLevel.toUpperCase()}
                    </Badge>
                    <span className="text-xs text-slate-500">{getFloodLevelDescription(location.predictedLevel)}</span>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}

        {/* No Results */}
        {showSuggestions && suggestions.length === 0 && searchTerm.length > 0 && !isLoading && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-white border rounded-lg shadow-lg z-10 p-4 text-center text-slate-500">
            No locations found for "{searchTerm}"
          </div>
        )}
      </div>

      {/* Quick Filters */}
      <div className="flex flex-wrap gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => handleQuickSelect("high-risk")}
          className="flex items-center space-x-1"
        >
          <AlertTriangle className="h-3 w-3 text-red-500" />
          <span>High Risk Areas</span>
          <Badge variant="destructive" className="ml-1 text-xs">
            {floodDataService.getHighRiskLocations().length}
          </Badge>
        </Button>

        <Button
          variant="outline"
          size="sm"
          onClick={() => handleQuickSelect("all")}
          className="flex items-center space-x-1"
        >
          <MapPin className="h-3 w-3" />
          <span>All Locations</span>
          <Badge variant="secondary" className="ml-1 text-xs">
            {allLocations.length}
          </Badge>
        </Button>

        {/* Region filters */}
        {["Northeast", "South", "West", "Midwest"].map((region) => (
          <Button
            key={region}
            variant="outline"
            size="sm"
            onClick={() => {
              const regionLocations = floodDataService.getLocationsByRegion(region)
              setSuggestions(regionLocations)
              setShowSuggestions(true)
              setSearchTerm("")
            }}
            className="text-xs"
          >
            {region}
            <Badge variant="outline" className="ml-1 text-xs">
              {floodDataService.getLocationsByRegion(region).length}
            </Badge>
          </Button>
        ))}
      </div>

      {/* Active Alerts Summary */}
      {floodDataService.getActiveAlerts().length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
          <div className="flex items-center space-x-2 mb-2">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            <span className="font-medium text-red-800">Active Flood Alerts</span>
            <Badge variant="destructive" className="text-xs">
              {floodDataService.getActiveAlerts().length}
            </Badge>
          </div>
          <div className="text-sm text-red-700">
            {floodDataService
              .getActiveAlerts()
              .slice(0, 2)
              .map((alert) => {
                const location = floodDataService.getLocationById(alert.locationId)
                return (
                  <div key={alert.id} className="mb-1">
                    <strong>{location?.name}:</strong> {alert.message}
                  </div>
                )
              })}
            {floodDataService.getActiveAlerts().length > 2 && (
              <div className="text-xs mt-1">+{floodDataService.getActiveAlerts().length - 2} more alerts</div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
