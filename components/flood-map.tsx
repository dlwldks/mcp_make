"use client"

import { useEffect, useRef, useState } from "react"
import { floodDataService, getFloodLevelColor, type FloodLocation } from "@/lib/flood-data-service"

interface FloodMapProps {
  selectedLocation: { lat: number; lng: number; name: string } | null
  onLocationSelect: (location: { lat: number; lng: number; name: string }) => void
  onFloodLevelChange: (current: number, predicted: number) => void
}

export function FloodMap({ selectedLocation, onLocationSelect, onFloodLevelChange }: FloodMapProps) {
  const mapRef = useRef<HTMLDivElement>(null)
  const [map, setMap] = useState<any>(null)
  const [markers, setMarkers] = useState<any[]>([])
  const [floodLocations, setFloodLocations] = useState<FloodLocation[]>([])

  useEffect(() => {
    const locations = floodDataService.getAllLocations()
    setFloodLocations(locations)
  }, [])

  useEffect(() => {
    if (typeof window === "undefined") return

    // Dynamically import Leaflet to avoid SSR issues
    import("leaflet").then((L) => {
      // Fix for default markers in Leaflet
      delete (L.Icon.Default.prototype as any)._getIconUrl
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
        iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
        shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
      })

      if (mapRef.current && !map && floodLocations.length > 0) {
        const newMap = L.map(mapRef.current).setView([39.8283, -98.5795], 4)

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution: "© OpenStreetMap contributors",
        }).addTo(newMap)

        const newMarkers = floodLocations.map((location) => {
          const color = getFloodLevelColor(location.predictedLevel)
          const trend = floodDataService.getFloodTrend(location.id)
          const trendIcon = trend === "rising" ? "↗" : trend === "falling" ? "↘" : "→"

          const marker = L.circleMarker([location.lat, location.lng], {
            radius: 8 + location.predictedLevel * 2,
            fillColor: color,
            color: "white",
            weight: 2,
            opacity: 1,
            fillOpacity: 0.7,
          }).addTo(newMap)

          marker.bindPopup(`
            <div className="p-3 min-w-48">
              <h3 className="font-bold text-lg">${location.name}</h3>
              <p className="text-sm text-gray-600 mb-2">${location.region} Region</p>
              <div className="space-y-1">
                <p><strong>Current:</strong> ${location.currentLevel.toFixed(1)}m</p>
                <p><strong>Predicted:</strong> ${location.predictedLevel.toFixed(1)}m ${trendIcon}</p>
                <p><strong>Risk Level:</strong> <span className="capitalize font-medium">${location.riskLevel}</span></p>
                <p className="text-xs text-gray-500">Updated: ${location.lastUpdated.toLocaleTimeString()}</p>
              </div>
            </div>
          `)

          marker.on("click", () => {
            onLocationSelect({
              lat: location.lat,
              lng: location.lng,
              name: location.name,
            })
            onFloodLevelChange(location.currentLevel, location.predictedLevel)
          })

          return marker
        })

        setMap(newMap)
        setMarkers(newMarkers)
      }
    })

    // Load Leaflet CSS
    const link = document.createElement("link")
    link.rel = "stylesheet"
    link.href = "https://unpkg.com/leaflet@1.7.1/dist/leaflet.css"
    document.head.appendChild(link)

    return () => {
      if (map) {
        map.remove()
      }
    }
  }, [floodLocations])

  useEffect(() => {
    if (map && selectedLocation) {
      map.setView([selectedLocation.lat, selectedLocation.lng], 10)
    }
  }, [map, selectedLocation])

  return (
    <div className="relative">
      <div ref={mapRef} className="h-96 w-full rounded-lg" />
      <div className="absolute top-4 right-4 bg-white p-2 rounded-lg shadow-lg">
        <div className="text-xs space-y-1">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span>Low Risk (&lt;2m)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-orange-500"></div>
            <span>Medium Risk (2-3m)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <span>High Risk (&gt;3m)</span>
          </div>
        </div>
      </div>
    </div>
  )
}
