"use client"

import { useEffect, useRef, useState } from "react"
import {
  floodDataService,
  getFloodLevelColor,
  getWeatherIcon,
  getWeatherColor,
  type FloodLocation,
} from "@/lib/flood-data-service"

interface CurrentConditionsMapProps {
  selectedLocation: { lat: number; lng: number; name: string } | null
  onLocationSelect: (location: { lat: number; lng: number; name: string }) => void
  onDataChange: (current: number, predicted: number) => void
}

export function CurrentConditionsMap({ selectedLocation, onLocationSelect, onDataChange }: CurrentConditionsMapProps) {
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

    import("leaflet").then((L) => {
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
          const floodColor = getFloodLevelColor(location.currentLevel)
          const weatherColor = getWeatherColor(location.currentWeather.condition)
          const weatherIcon = getWeatherIcon(location.currentWeather.condition)

          // Create a custom marker with both flood and weather info
          const marker = L.circleMarker([location.lat, location.lng], {
            radius: 10,
            fillColor: floodColor,
            color: weatherColor,
            weight: 3,
            opacity: 1,
            fillOpacity: 0.7,
          }).addTo(newMap)

          marker.bindPopup(`
            <div className="p-3 min-w-56">
              <h3 className="font-bold text-lg">${location.name}</h3>
              <p className="text-sm text-gray-600 mb-3">${location.region} Region</p>
              
              <div className="mb-3">
                <h4 className="font-semibold text-sm mb-1">Current Weather</h4>
                <div className="flex items-center space-x-2 text-sm">
                  <span className="text-lg">${weatherIcon}</span>
                  <span>${location.currentWeather.temperature}°C</span>
                  <span className="capitalize">${location.currentWeather.condition}</span>
                </div>
                <div className="text-xs text-gray-600 mt-1">
                  <p>Humidity: ${location.currentWeather.humidity}% | Wind: ${location.currentWeather.windSpeed} km/h</p>
                  <p>Precipitation: ${location.currentWeather.precipitation}mm</p>
                </div>
              </div>
              
              <div>
                <h4 className="font-semibold text-sm mb-1">Flood Status</h4>
                <div className="space-y-1 text-sm">
                  <p><strong>Current Level:</strong> ${location.currentLevel.toFixed(1)}m</p>
                  <p><strong>Risk Level:</strong> <span className="capitalize font-medium">${location.riskLevel}</span></p>
                </div>
              </div>
              
              <p className="text-xs text-gray-500 mt-2">Updated: ${location.lastUpdated.toLocaleTimeString()}</p>
            </div>
          `)

          marker.on("click", () => {
            onLocationSelect({
              lat: location.lat,
              lng: location.lng,
              name: location.name,
            })
            onDataChange(location.currentLevel, location.predictedLevel)
          })

          return marker
        })

        setMap(newMap)
        setMarkers(newMarkers)
      }
    })

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
      <div className="absolute top-4 right-4 bg-white p-3 rounded-lg shadow-lg">
        <h4 className="font-semibold text-sm mb-2">Current Conditions</h4>
        <div className="text-xs space-y-2">
          <div>
            <p className="font-medium mb-1">Flood Risk</p>
            <div className="space-y-1">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
                <span>Low (&lt;2m)</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-orange-500"></div>
                <span>Medium (2-3m)</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-red-500"></div>
                <span>High (&gt;3m)</span>
              </div>
            </div>
          </div>
          <div>
            <p className="font-medium mb-1">Weather</p>
            <div className="space-y-1">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: "#FCD34D" }}></div>
                <span>Sunny</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: "#9CA3AF" }}></div>
                <span>Cloudy</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: "#3B82F6" }}></div>
                <span>Rainy</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: "#7C3AED" }}></div>
                <span>Stormy</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
