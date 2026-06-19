import { useCallback, useMemo, useState } from 'react'
import { useCurrentPosition, useWatchPosition } from 'react-use-geolocation'
import type { GpsPayload } from '../types/domain'

const GPS_OPTIONS: PositionOptions = {
  enableHighAccuracy: true,
  maximumAge: 15000,
  timeout: 12000,
}

export function useGpsCapture() {
  const [currentPosition, currentError] = useCurrentPosition(GPS_OPTIONS)
  const [watchedPosition, watchedError] = useWatchPosition(GPS_OPTIONS)
  const [manualPosition, setManualPosition] = useState<GeolocationPosition | null>(null)
  const [manualError, setManualError] = useState<GeolocationPositionError | null>(null)
  const [refreshing, setRefreshing] = useState(false)

  const position = manualPosition ?? watchedPosition ?? currentPosition ?? null
  const error = manualError ?? watchedError ?? currentError ?? null

  const gps = useMemo<GpsPayload | null>(() => {
    if (!position) {
      return null
    }
    return {
      latitude: position.coords.latitude,
      longitude: position.coords.longitude,
      precisao_metros: position.coords.accuracy ?? null,
    }
  }, [position])

  const refresh = useCallback(async () => {
    if (!navigator.geolocation) {
      return
    }
    setRefreshing(true)
    setManualError(null)
    navigator.geolocation.getCurrentPosition(
      (nextPosition) => {
        setManualPosition(nextPosition)
        setRefreshing(false)
      },
      (nextError) => {
        setManualError(nextError)
        setRefreshing(false)
      },
      GPS_OPTIONS,
    )
  }, [])

  return {
    gps,
    error,
    refreshing,
    refresh,
  }
}
