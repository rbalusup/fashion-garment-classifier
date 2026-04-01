import { useRef, useState } from 'react'
import { uploadGarment } from '@/api/client'
import type { GarmentOut } from '@/types/garment'

interface Props {
  onClose: () => void
  onSuccess: (garment: GarmentOut) => void
}

export function UploadModal({ onClose, onSuccess }: Props) {
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [continent, setContinent] = useState('')
  const [country, setCountry] = useState('')
  const [city, setCity] = useState('')
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = (f: File) => {
    setFile(f)
    const url = URL.createObjectURL(f)
    setPreview(url)
    setError(null)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const f = e.dataTransfer.files[0]
    if (f) handleFile(f)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) return
    setUploading(true)
    setError(null)
    try {
      const result = await uploadGarment(file, { continent, country, city })
      onSuccess(result)
    } catch (err) {
      setError(String(err))
    } finally {
      setUploading(false)
    }
  }

  return (
    <div
      className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      onClick={e => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Upload Garment</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Drop zone */}
          <div
            className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors ${
              file ? 'border-indigo-400 bg-indigo-50' : 'border-gray-300 hover:border-indigo-300'
            }`}
            onDrop={handleDrop}
            onDragOver={e => e.preventDefault()}
            onClick={() => inputRef.current?.click()}
          >
            <input
              ref={inputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])}
            />
            {preview ? (
              <img src={preview} alt="preview" className="max-h-40 mx-auto rounded-lg object-contain" />
            ) : (
              <div className="space-y-1">
                <p className="text-3xl">📸</p>
                <p className="text-sm text-gray-500">Drag & drop or click to select</p>
                <p className="text-xs text-gray-400">JPEG, PNG, WebP</p>
              </div>
            )}
          </div>

          {/* Location metadata */}
          <div className="grid grid-cols-3 gap-2">
            <input
              type="text"
              placeholder="Continent"
              value={continent}
              onChange={e => setContinent(e.target.value)}
              className="border rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
            />
            <input
              type="text"
              placeholder="Country"
              value={country}
              onChange={e => setCountry(e.target.value)}
              className="border rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
            />
            <input
              type="text"
              placeholder="City"
              value={city}
              onChange={e => setCity(e.target.value)}
              className="border rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
            />
          </div>

          {error && <p className="text-sm text-red-500">{error}</p>}

          <button
            type="submit"
            disabled={!file || uploading}
            className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-medium py-2 rounded-lg transition-colors"
          >
            {uploading ? 'Classifying with AI…' : 'Upload & Classify'}
          </button>
        </form>
      </div>
    </div>
  )
}
