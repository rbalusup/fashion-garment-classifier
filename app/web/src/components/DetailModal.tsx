import { useEffect, useState } from 'react'
import { getGarment } from '@/api/client'
import type { GarmentOut } from '@/types/garment'
import { AnnotationPanel } from './AnnotationPanel'

interface Props {
  garmentId: number
  onClose: () => void
  onAnnotationChange: () => void
}

function Badge({ label, variant }: { label: string; variant: 'ai' | 'designer' }) {
  return variant === 'ai' ? (
    <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
      🤖 AI
    </span>
  ) : (
    <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">
      ✏️ {label}
    </span>
  )
}

function Attr({ label, value }: { label: string; value: string | null | undefined }) {
  if (!value) return null
  return (
    <div className="flex gap-2 items-start">
      <span className="text-xs text-gray-400 w-28 shrink-0">{label}</span>
      <span className="text-xs text-gray-700 capitalize">{value}</span>
    </div>
  )
}

function ColorChips({ colors }: { colors: string[] }) {
  return (
    <div className="flex gap-1 flex-wrap mt-1">
      {colors.map(c => {
        const isHex = /^#[0-9a-f]{3,6}$/i.test(c)
        return (
          <span
            key={c}
            className="text-xs px-2 py-0.5 rounded-full border text-gray-600"
            style={isHex ? { backgroundColor: c, color: 'transparent', borderColor: c } : {}}
          >
            {isHex ? '  ' : c}
          </span>
        )
      })}
    </div>
  )
}

export function DetailModal({ garmentId, onClose, onAnnotationChange }: Props) {
  const [garment, setGarment] = useState<GarmentOut | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getGarment(garmentId)
      .then(setGarment)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [garmentId])

  return (
    <div
      className="fixed inset-0 bg-black/60 z-50 flex items-start justify-center p-4 overflow-y-auto"
      onClick={e => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl my-8 flex flex-col md:flex-row overflow-hidden">
        {/* Left: Image */}
        <div className="md:w-2/5 bg-gray-100 flex items-center justify-center min-h-64">
          {loading ? (
            <div className="animate-pulse w-full h-64 bg-gray-200" />
          ) : garment ? (
            <img
              src={`/${garment.imagePath}`}
              alt={garment.garmentType ?? 'garment'}
              className="w-full h-full object-cover"
            />
          ) : (
            <p className="text-gray-400">Not found</p>
          )}
        </div>

        {/* Right: Metadata */}
        <div className="md:w-3/5 p-6 space-y-5 overflow-y-auto max-h-[80vh]">
          <div className="flex items-start justify-between">
            <h2 className="text-base font-semibold text-gray-800 leading-tight">
              {garment?.originalFilename ?? '…'}
            </h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl ml-4">
              ✕
            </button>
          </div>

          {garment && (
            <>
              {/* AI Classification */}
              <section className="bg-blue-50 border-l-4 border-blue-400 rounded-r-lg p-4 space-y-3">
                <div className="flex items-center gap-2">
                  <Badge label="AI" variant="ai" />
                  <span className="text-xs text-blue-600 font-medium">Classification</span>
                </div>
                {garment.description && (
                  <p className="text-xs text-gray-600 leading-relaxed">{garment.description}</p>
                )}
                <div className="space-y-1.5">
                  <Attr label="Garment Type" value={garment.garmentType} />
                  <Attr label="Style" value={garment.style} />
                  <Attr label="Material" value={garment.material} />
                  <Attr label="Pattern" value={garment.pattern} />
                  <Attr label="Season" value={garment.season} />
                  <Attr label="Occasion" value={garment.occasion} />
                  <Attr label="Consumer Profile" value={garment.consumerProfile} />
                  {garment.colorPalette.length > 0 && (
                    <div className="flex gap-2 items-start">
                      <span className="text-xs text-gray-400 w-28 shrink-0">Colors</span>
                      <ColorChips colors={garment.colorPalette} />
                    </div>
                  )}
                  {garment.trendNotes && (
                    <div className="pt-1 border-t border-blue-100">
                      <p className="text-xs text-gray-500 italic">{garment.trendNotes}</p>
                    </div>
                  )}
                </div>

                {/* Location & time */}
                <div className="pt-1 border-t border-blue-100 grid grid-cols-2 gap-1">
                  <Attr label="Continent" value={garment.locationContinent} />
                  <Attr label="Country" value={garment.locationCountry} />
                  <Attr label="City" value={garment.locationCity} />
                  <Attr label="Year" value={garment.year?.toString()} />
                </div>

                {garment.classificationError && (
                  <p className="text-xs text-red-500">⚠ {garment.classificationError}</p>
                )}
              </section>

              {/* Designer Annotations */}
              <section className="bg-amber-50 border-l-4 border-amber-400 rounded-r-lg p-4 space-y-3">
                <div className="flex items-center gap-2">
                  <Badge label="Designer" variant="designer" />
                  <span className="text-xs text-amber-700 font-medium">Notes</span>
                </div>
                <AnnotationPanel
                  garmentId={garment.id}
                  onChange={onAnnotationChange}
                />
              </section>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
