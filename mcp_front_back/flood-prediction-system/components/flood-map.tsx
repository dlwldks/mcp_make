

/**
 * 🗺️ FloodMap 컴포넌트
 *
 * 📌 이 컴포넌트는 Leaflet.js를 사용해 지도 위에 홍수 위험 지역을 시각적으로 표시합니다.
 * - 각 마커는 지역별 현재 수위 및 예측 수위를 반영하여 색상과 크기로 표시됩니다.
 * - 마커 클릭 시 상세 정보 팝업이 나타나고, 선택된 위치의 수위 정보를 부모로 전달합니다.
 * - 클릭한 지역은 확대되며 `onLocationSelect` 및 `onFloodLevelChange` 콜백이 작동합니다.
 *
 * ✅ 주요 기능:
 * - Leaflet를 이용한 대화형 지도 렌더링
 * - 실시간 수위 데이터에 따라 마커 색상 및 크기 조절
 * - 지역별 예측 수위에 따라 "↗", "↘", "→" 등 수위 추세 아이콘 표시
 * - 마커 클릭 시: 지역 선택 및 현재/예측 수위 전달
 * - 지도 우측 상단에 수위 범례(리스크 레벨) 표시
 *
 * 🧩 Props:
 * - `selectedLocation`: 선택된 위치 (lat, lng, name 포함)
 * - `onLocationSelect`: 사용자가 마커 클릭 시 선택된 위치 정보를 부모 컴포넌트로 전달
 * - `onFloodLevelChange`: 선택된 위치의 현재 수위와 예측 수위를 부모로 전달
 *
 * 📦 내부 상태:
 * - `mapRef`: 지도 DOM을 참조
 * - `map`: Leaflet 지도 인스턴스
 * - `markers`: 생성된 마커 배열
 * - `floodLocations`: floodDataService에서 받아온 홍수 지역 리스트
 *
 * 📦 의존 라이브러리:
 * - `leaflet`: 지도 시각화 및 마커 생성
 * - `@/lib/flood-data-service`: 홍수 데이터 관리 (예: 수위 예측, 추세 분석 등)
 *
 * 🛠️ 처리 흐름:
 * 1. floodDataService에서 전체 위치 데이터를 받아와 상태 저장
 * 2. 클라이언트 환경에서 Leaflet 동적 import 후 지도 생성
 * 3. 각 위치에 대해 circleMarker 생성, 색상 및 크기 설정
 * 4. 클릭 이벤트 바인딩: 선택된 위치 상태 변경 + 수위 정보 전달
 * 5. selectedLocation prop이 변경되면 해당 위치로 지도를 이동
 * 6. Leaflet CSS를 동적으로 로드
 *
 * 📌 참고:
 * - 위험도 색상 기준은 다음과 같습니다:
 *   - 초록색: <2m (Low Risk)
 *   - 주황색: 2~3m (Medium Risk)
 *   - 빨간색: >3m (High Risk)
 */


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
            <div class="p-3 min-w-48">
              <h3 class="font-bold text-lg">${location.name}</h3>
              <p class="text-sm text-gray-600 mb-2">${location.region} Region</p>
              <div class="space-y-1">
                <p><strong>Current:</strong> ${location.currentLevel.toFixed(1)}m</p>
                <p><strong>Predicted:</strong> ${location.predictedLevel.toFixed(1)}m ${trendIcon}</p>
                <p><strong>Risk Level:</strong> <span class="capitalize font-medium">${location.riskLevel}</span></p>
                <p class="text-xs text-gray-500">Updated: ${location.lastUpdated.toLocaleTimeString()}</p>
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
