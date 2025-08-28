export interface FloodLocation {
  id: string
  lat: number
  lng: number
  name: string
  region: string
  riskLevel: "low" | "medium" | "high"
  currentLevel: number
  predictedLevel: number
  historicalData: FloodReading[]
  lastUpdated: Date
}

export interface FloodReading {
  timestamp: Date
  level: number
  rainfall: number
  temperature: number
}

export interface FloodAlert {
  id: string
  locationId: string
  severity: "watch" | "warning" | "emergency"
  message: string
  issuedAt: Date
  expiresAt: Date
}

class FloodDataService {
  private locations: FloodLocation[] = []
  private alerts: FloodAlert[] = []

  constructor() {
    this.initializeData()
  }

  private initializeData() {
    // Generate comprehensive flood data for multiple locations
    const baseLocations = [
      { lat: 40.7128, lng: -74.006, name: "New York City", region: "Northeast" },
      { lat: 29.7604, lng: -95.3698, name: "Houston", region: "South" },
      { lat: 25.7617, lng: -80.1918, name: "Miami", region: "Southeast" },
      { lat: 47.6062, lng: -122.3321, name: "Seattle", region: "Northwest" },
      { lat: 39.9526, lng: -75.1652, name: "Philadelphia", region: "Northeast" },
      { lat: 29.9511, lng: -90.0715, name: "New Orleans", region: "South" },
      { lat: 41.8781, lng: -87.6298, name: "Chicago", region: "Midwest" },
      { lat: 37.7749, lng: -122.4194, name: "San Francisco", region: "West" },
    ]

    this.locations = baseLocations.map((loc, index) => {
      const currentLevel = this.generateRealisticFloodLevel()
      const predictedLevel = this.generatePrediction(currentLevel)
      const historicalData = this.generateHistoricalData()

      return {
        id: `loc_${index + 1}`,
        ...loc,
        riskLevel: this.calculateRiskLevel(predictedLevel),
        currentLevel,
        predictedLevel,
        historicalData,
        lastUpdated: new Date(),
      }
    })

    this.generateAlerts()
  }

  private generateRealisticFloodLevel(): number {
    // Generate more realistic flood levels based on seasonal patterns
    const baseLevel = Math.random() * 2 + 0.5 // 0.5 to 2.5m base
    const seasonalVariation = Math.sin((Date.now() / (1000 * 60 * 60 * 24 * 365)) * 2 * Math.PI) * 0.5
    const weatherNoise = (Math.random() - 0.5) * 1.0

    return Math.max(0.1, baseLevel + seasonalVariation + weatherNoise)
  }

  private generatePrediction(currentLevel: number): number {
    // Simulate prediction algorithm with trend analysis
    const trend = (Math.random() - 0.4) * 2 // Slight bias toward increase
    const uncertainty = Math.random() * 0.5
    const predicted = currentLevel + trend + uncertainty

    return Math.max(0.1, predicted)
  }

  private generateHistoricalData(): FloodReading[] {
    const data: FloodReading[] = []
    const now = new Date()

    // Generate 30 days of historical data
    for (let i = 30; i >= 0; i--) {
      const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000)
      data.push({
        timestamp: date,
        level: this.generateRealisticFloodLevel(),
        rainfall: Math.random() * 50, // mm
        temperature: 15 + Math.random() * 20, // 15-35°C
      })
    }

    return data
  }

  private calculateRiskLevel(predictedLevel: number): "low" | "medium" | "high" {
    if (predictedLevel < 2) return "low"
    if (predictedLevel < 3.5) return "medium"
    return "high"
  }

  private generateAlerts() {
    this.alerts = this.locations
      .filter((loc) => loc.riskLevel === "high" || (loc.riskLevel === "medium" && Math.random() > 0.5))
      .map((loc) => ({
        id: `alert_${loc.id}`,
        locationId: loc.id,
        severity: loc.riskLevel === "high" ? "warning" : ("watch" as const),
        message:
          loc.riskLevel === "high"
            ? `Flood warning in effect for ${loc.name}. Expected level: ${loc.predictedLevel.toFixed(1)}m`
            : `Flood watch for ${loc.name}. Monitor conditions closely.`,
        issuedAt: new Date(),
        expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000), // 24 hours
      }))
  }

  // Public API methods
  getAllLocations(): FloodLocation[] {
    return [...this.locations]
  }

  getLocationById(id: string): FloodLocation | undefined {
    return this.locations.find((loc) => loc.id === id)
  }

  getLocationsByRegion(region: string): FloodLocation[] {
    return this.locations.filter((loc) => loc.region === region)
  }

  getHighRiskLocations(): FloodLocation[] {
    return this.locations.filter((loc) => loc.riskLevel === "high")
  }

  getActiveAlerts(): FloodAlert[] {
    const now = new Date()
    return this.alerts.filter((alert) => alert.expiresAt > now)
  }

  getAlertsForLocation(locationId: string): FloodAlert[] {
    return this.alerts.filter((alert) => alert.locationId === locationId)
  }

  updateFloodData(): void {
    // Simulate real-time data updates
    this.locations.forEach((location) => {
      location.currentLevel = this.generateRealisticFloodLevel()
      location.predictedLevel = this.generatePrediction(location.currentLevel)
      location.riskLevel = this.calculateRiskLevel(location.predictedLevel)
      location.lastUpdated = new Date()

      // Add new historical reading
      location.historicalData.push({
        timestamp: new Date(),
        level: location.currentLevel,
        rainfall: Math.random() * 50,
        temperature: 15 + Math.random() * 20,
      })

      // Keep only last 30 days
      if (location.historicalData.length > 30) {
        location.historicalData = location.historicalData.slice(-30)
      }
    })

    this.generateAlerts()
  }

  getFloodTrend(locationId: string, days = 7): "rising" | "falling" | "stable" {
    const location = this.getLocationById(locationId)
    if (!location) return "stable"

    const recentData = location.historicalData.slice(-days)
    if (recentData.length < 2) return "stable"

    const firstLevel = recentData[0].level
    const lastLevel = recentData[recentData.length - 1].level
    const difference = lastLevel - firstLevel

    if (difference > 0.3) return "rising"
    if (difference < -0.3) return "falling"
    return "stable"
  }

  searchLocations(query: string): FloodLocation[] {
    const lowercaseQuery = query.toLowerCase()
    return this.locations.filter(
      (loc) => loc.name.toLowerCase().includes(lowercaseQuery) || loc.region.toLowerCase().includes(lowercaseQuery),
    )
  }
}

// Export singleton instance
export const floodDataService = new FloodDataService()

// Export utility functions
export function getFloodLevelColor(level: number): string {
  if (level < 2) return "#10b981" // green
  if (level < 3.5) return "#f59e0b" // orange
  return "#ef4444" // red
}

export function getFloodLevelDescription(level: number): string {
  if (level < 1) return "Very Low"
  if (level < 2) return "Low"
  if (level < 3) return "Moderate"
  if (level < 4) return "High"
  return "Critical"
}

export function formatFloodLevel(level: number): string {
  return `${level.toFixed(1)}m`
}
