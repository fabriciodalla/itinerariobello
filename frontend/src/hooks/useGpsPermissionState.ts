import { useEffect, useState } from 'react'

export type GpsPermissionState = 'granted' | 'denied' | 'prompt' | 'unsupported'

export function useGpsPermissionState(): GpsPermissionState {
  const [state, setState] = useState<GpsPermissionState>('prompt')

  useEffect(() => {
    if (!navigator.geolocation) {
      setState('unsupported')
      return
    }
    if (!navigator.permissions?.query) {
      return
    }

    let active = true
    let status: PermissionStatus | null = null

    navigator.permissions
      .query({ name: 'geolocation' })
      .then((permissionStatus) => {
        if (!active) return
        status = permissionStatus
        setState(permissionStatus.state as GpsPermissionState)
        permissionStatus.onchange = () => setState(permissionStatus.state as GpsPermissionState)
      })
      .catch(() => undefined)

    return () => {
      active = false
      if (status) status.onchange = null
    }
  }, [])

  return state
}
