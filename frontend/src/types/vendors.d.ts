declare module 'react-use-geolocation' {
  export function useCurrentPosition(
    options?: PositionOptions,
  ): [GeolocationPosition | undefined, GeolocationPositionError | undefined]

  export function useWatchPosition(
    options?: PositionOptions,
  ): [GeolocationPosition | undefined, GeolocationPositionError | undefined]
}

declare module 'virtual:pwa-register' {
  export function registerSW(options?: { immediate?: boolean }): (reloadPage?: boolean) => Promise<void>
}
