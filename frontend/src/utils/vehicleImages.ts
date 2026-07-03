const vehicleImageModules = import.meta.glob('../assets/carros/*.{png,webp,jpg,jpeg}', {
  eager: true,
  import: 'default',
  query: '?url',
}) as Record<string, string>

const MODEL_IMAGE_ALIASES: Record<string, string> = {
  corolla: 'corola',
  renegade: 'renagade',
}

const vehicleImagesByModel = Object.entries(vehicleImageModules).reduce<Record<string, string>>((acc, [path, url]) => {
  const filename = path.split('/').pop() ?? ''
  const model = filename.replace(/\.[^.]+$/, '')
  acc[normalizeVehicleModel(model)] = url
  return acc
}, {})

export function vehicleImageForModel(model: string) {
  const normalizedModel = normalizeVehicleModel(model)
  if (!normalizedModel) {
    return null
  }

  const directKey = MODEL_IMAGE_ALIASES[normalizedModel] ?? normalizedModel
  if (vehicleImagesByModel[directKey]) {
    return vehicleImagesByModel[directKey]
  }

  const imageKey = Object.keys(vehicleImagesByModel)
    .sort((a, b) => b.length - a.length)
    .find((candidate) => normalizedModel.includes(candidate) || candidate.includes(normalizedModel))

  return imageKey ? vehicleImagesByModel[imageKey] : null
}

function normalizeVehicleModel(value: string) {
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/\b(chevrolet|dodge|fiat|ford|honda|hyundai|jeep|kia|renault|toyota|volkswagen|vw)\b/g, ' ')
    .replace(/[^a-z0-9]+/g, '')
}
