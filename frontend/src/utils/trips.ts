import type { PhotoEvidence, Trip, Vehicle } from '../types/domain'

type TripVehicleFields = Pick<Trip, 'veiculo_placa' | 'veiculo_modelo'>
type VehicleLabelFields = Pick<Vehicle, 'placa' | 'modelo'>

export function tripVehicleLabel(trip: TripVehicleFields, vehicle?: VehicleLabelFields | null) {
  const placa = normalizeText(trip.veiculo_placa || vehicle?.placa)
  const modelo = normalizeText(trip.veiculo_modelo || vehicle?.modelo)

  if (placa && modelo) {
    return `${placa} | ${modelo}`
  }
  if (placa) {
    return placa
  }
  if (modelo) {
    return modelo
  }
  return 'Veiculo nao identificado'
}

export function photoEvidenceFromListItem(photo: PhotoEvidence): PhotoEvidence {
  return {
    ...photo,
    download_url: photo.download_url || `/photos/${photo.id}`,
  }
}

function normalizeText(value: string | null | undefined) {
  return (value ?? '').trim()
}
