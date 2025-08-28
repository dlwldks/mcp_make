export interface WeatherCondition {
  temperature: number
  condition: "sunny" | "cloudy" | "rainy" | "stormy"
  humidity: number
  windSpeed: number
  precipitation: number
}

export interface WeatherForecast {
  date: Date
  temperature: { min: number; max: number }
  condition: "sunny" | "cloudy" | "rainy" | "stormy"
  precipitation: number
  floodRisk: number // 0-1 scale
}

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
  currentWeather: WeatherCondition
  weatherForecast: WeatherForecast[]
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
      { lat: 37.5665, lng: 126.978, name: "Seoul", region: "Seoul Capital Area" },
      { lat: 35.1796, lng: 129.0756, name: "Busan", region: "Gyeongsang Province" },
      { lat: 37.4563, lng: 126.7052, name: "Incheon", region: "Seoul Capital Area" },
      { lat: 35.8714, lng: 128.6014, name: "Daegu", region: "Gyeongsang Province" },
      { lat: 36.3504, lng: 127.3845, name: "Daejeon", region: "Chungcheong Province" },
      { lat: 35.1595, lng: 126.8526, name: "Gwangju", region: "Jeolla Province" },
      { lat: 35.5384, lng: 129.3114, name: "Ulsan", region: "Gyeongsang Province" },
      { lat: 37.2636, lng: 127.0286, name: "Suwon", region: "Seoul Capital Area" },
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
        currentWeather: this.generateCurrentWeather(),
        weatherForecast: this.generateWeatherForecast(),
      }
    })

    this.generateAlerts()
  }

  private generateCurrentWeather(): WeatherCondition {
    const conditions: WeatherCondition["condition"][] = ["sunny", "cloudy", "rainy", "stormy"]
    const condition = conditions[Math.floor(Math.random() * conditions.length)]

    return {
      temperature: Math.round(15 + Math.random() * 20), // 15-35°C
      condition,
      humidity: Math.round(30 + Math.random() * 60), // 30-90%
      windSpeed: Math.round(Math.random() * 30), // 0-30 km/h
      precipitation: condition === "rainy" || condition === "stormy" ? Math.round(Math.random() * 20) : 0,
    }
  }

  private generateWeatherForecast(): WeatherForecast[] {
    const forecast: WeatherForecast[] = []
    const conditions: WeatherForecast["condition"][] = ["sunny", "cloudy", "rainy", "stormy"]

    for (let i = 0; i < 7; i++) {
      const date = new Date()
      date.setDate(date.getDate() + i)

      const condition = conditions[Math.floor(Math.random() * conditions.length)]
      const baseTemp = 15 + Math.random() * 20
      const precipitation = condition === "rainy" || condition === "stormy" ? Math.random() * 30 : Math.random() * 5

      forecast.push({
        date,
        temperature: {
          min: Math.round(baseTemp - 5),
          max: Math.round(baseTemp + 5),
        },
        condition,
        precipitation: Math.round(precipitation),
        floodRisk: this.calculateFloodRisk(condition, precipitation),
      })
    }

    return forecast
  }

  private calculateFloodRisk(condition: WeatherCondition["condition"], precipitation: number): number {
    let baseRisk = 0.1

    switch (condition) {
      case "sunny":
        baseRisk = 0.05
        break
      case "cloudy":
        baseRisk = 0.15
        break
      case "rainy":
        baseRisk = 0.4
        break
      case "stormy":
        baseRisk = 0.7
        break
    }

    // Increase risk based on precipitation
    const precipitationRisk = Math.min(precipitation / 50, 0.3)

    return Math.min(baseRisk + precipitationRisk, 1)
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
      location.currentWeather = this.generateCurrentWeather()

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

export function getWeatherIcon(condition: WeatherCondition["condition"]): string {
  switch (condition) {
    case "sunny":
      return "☀️"
    case "cloudy":
      return "☁️"
    case "rainy":
      return "🌧️"
    case "stormy":
      return "⛈️"
    default:
      return "🌤️"
  }
}

export function getWeatherColor(condition: WeatherCondition["condition"]): string {
  switch (condition) {
    case "sunny":
      return "#FCD34D" // yellow
    case "cloudy":
      return "#9CA3AF" // gray
    case "rainy":
      return "#3B82F6" // blue
    case "stormy":
      return "#7C3AED" // purple
    default:
      return "#6B7280" // neutral gray
  }
}
