import { useEffect, useRef, useState } from 'react'
import { CameraIcon, Loader2, RotateCcw, Upload } from 'lucide-react'

interface CameraCaptureProps {
  label: string
  file: File | null
  onFileChange: (file: File | null) => void
}

const MAX_PHOTO_BYTES = 4.8 * 1024 * 1024
const MAX_PHOTO_SIDE = 1600
const JPEG_QUALITIES = [0.82, 0.74, 0.66, 0.58]

export function CameraCapture({ label, file, onFileChange }: CameraCaptureProps) {
  const cameraInputRef = useRef<HTMLInputElement | null>(null)
  const galleryInputRef = useRef<HTMLInputElement | null>(null)
  const previewUrlRef = useRef('')
  const [preparing, setPreparing] = useState(false)
  const [previewUrl, setPreviewUrl] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    if (!file && previewUrlRef.current) {
      URL.revokeObjectURL(previewUrlRef.current)
      previewUrlRef.current = ''
      setPreviewUrl('')
    }
  }, [file])

  useEffect(() => {
    return () => {
      if (previewUrlRef.current) {
        URL.revokeObjectURL(previewUrlRef.current)
      }
    }
  }, [])

  async function selectFile(nextFile: File | undefined, input: HTMLInputElement | null) {
    if (!nextFile) {
      return
    }

    setPreparing(true)
    setError('')
    try {
      const preparedFile = await preparePhotoFile(nextFile)
      setPhotoFile(preparedFile)
    } catch {
      setError('Nao foi possivel preparar a foto. Use JPG, PNG ou WEBP.')
    } finally {
      setPreparing(false)
      if (input) {
        input.value = ''
      }
    }
  }

  function setPhotoFile(nextFile: File) {
    clearPreview()
    const nextPreviewUrl = URL.createObjectURL(nextFile)
    previewUrlRef.current = nextPreviewUrl
    setPreviewUrl(nextPreviewUrl)
    onFileChange(nextFile)
  }

  function clearPreview() {
    if (previewUrlRef.current) {
      URL.revokeObjectURL(previewUrlRef.current)
    }
    previewUrlRef.current = ''
    setPreviewUrl('')
  }

  function clearPhoto() {
    clearPreview()
    setError('')
    onFileChange(null)
  }

  return (
    <div className={`capture-block ${file ? 'is-ready' : ''}`}>
      <div className="field-header">
        <span>{label}</span>
        {file ? <span className="field-ok">foto pronta</span> : <span className="field-warn">obrigatoria</span>}
      </div>

      {previewUrl ? (
        <div className="photo-preview">
          <img src={previewUrl} alt="Foto do hodometro" />
        </div>
      ) : (
        <div className="photo-placeholder" aria-hidden="true">
          <CameraIcon />
          <span>Hodometro</span>
        </div>
      )}

      {error ? <div className="inline-error">{error}</div> : null}

      <div className="action-row capture-actions">
        <button
          className="primary-button compact"
          type="button"
          onClick={() => cameraInputRef.current?.click()}
          disabled={preparing}
        >
          {preparing ? <Loader2 className="spin" /> : <CameraIcon />}
          <span>{preparing ? 'Preparando' : 'Camera'}</span>
        </button>
        <button
          className="secondary-button compact"
          type="button"
          onClick={() => galleryInputRef.current?.click()}
          disabled={preparing}
        >
          <Upload />
          <span>Galeria</span>
        </button>
        {file ? (
          <button className="ghost-button icon-only" type="button" onClick={clearPhoto} aria-label="Limpar foto">
            <RotateCcw />
          </button>
        ) : null}
      </div>

      <input
        ref={cameraInputRef}
        className="hidden-file-input"
        type="file"
        accept="image/*"
        capture="environment"
        onChange={(event) => void selectFile(event.target.files?.[0], event.currentTarget)}
      />
      <input
        ref={galleryInputRef}
        className="hidden-file-input"
        type="file"
        accept="image/*"
        onChange={(event) => void selectFile(event.target.files?.[0], event.currentTarget)}
      />
    </div>
  )
}

async function preparePhotoFile(file: File): Promise<File> {
  if (file.type === 'image/jpeg' && file.size <= MAX_PHOTO_BYTES) {
    return file
  }

  const image = await loadImage(file)
  const { width, height } = fitInside(image.naturalWidth, image.naturalHeight, MAX_PHOTO_SIDE)
  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const context = canvas.getContext('2d')
  if (!context) {
    throw new Error('Canvas indisponivel.')
  }

  context.drawImage(image, 0, 0, width, height)

  for (const quality of JPEG_QUALITIES) {
    const blob = await canvasToBlob(canvas, quality)
    if (blob.size <= MAX_PHOTO_BYTES || quality === JPEG_QUALITIES[JPEG_QUALITIES.length - 1]) {
      return new File([blob], `hodometro-${Date.now()}.jpg`, { type: 'image/jpeg' })
    }
  }

  throw new Error('Nao foi possivel compactar a foto.')
}

function loadImage(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file)
    const image = new window.Image()
    image.onload = () => {
      URL.revokeObjectURL(url)
      resolve(image)
    }
    image.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('Imagem invalida.'))
    }
    image.src = url
  })
}

function fitInside(width: number, height: number, maxSide: number) {
  if (width <= maxSide && height <= maxSide) {
    return { width, height }
  }
  const ratio = Math.min(maxSide / width, maxSide / height)
  return {
    width: Math.round(width * ratio),
    height: Math.round(height * ratio),
  }
}

function canvasToBlob(canvas: HTMLCanvasElement, quality: number): Promise<Blob> {
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => {
        if (blob) {
          resolve(blob)
        } else {
          reject(new Error('Blob invalido.'))
        }
      },
      'image/jpeg',
      quality,
    )
  })
}
