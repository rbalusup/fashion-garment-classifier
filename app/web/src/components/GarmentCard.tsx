import type { GarmentListItem } from '@/types/garment'

interface Props {
  garment: GarmentListItem
  onClick: () => void
}

function ColorChips({ colors }: { colors: string[] }) {
  return (
    <div className="flex gap-1 flex-wrap">
      {colors.slice(0, 4).map(c => {
        const isHex = /^#[0-9a-f]{3,6}$/i.test(c)
        return (
          <span
            key={c}
            className="text-xs px-1.5 py-0.5 rounded-full border border-gray-200 text-gray-600"
            style={isHex ? { backgroundColor: c, color: 'transparent' } : {}}
            title={c}
          >
            {isHex ? '  ' : c}
          </span>
        )
      })}
    </div>
  )
}

export function GarmentCard({ garment, onClick }: Props) {
  return (
    <div
      className="group cursor-pointer rounded-xl overflow-hidden bg-white shadow-sm hover:shadow-md transition-shadow border border-gray-100"
      onClick={onClick}
    >
      <div className="aspect-[3/4] overflow-hidden bg-gray-100">
        <img
          src={`/${garment.imagePath}`}
          alt={garment.garmentType ?? 'garment'}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          loading="lazy"
          onError={e => {
            (e.target as HTMLImageElement).src =
              'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="120" fill="%23e5e7eb"><rect width="100" height="120"/><text x="50%" y="50%" text-anchor="middle" fill="%239ca3af" font-size="12">No image</text></svg>'
          }}
        />
      </div>
      <div className="p-3 space-y-1.5">
        <div className="flex items-center justify-between gap-2">
          {garment.garmentType ? (
            <span className="text-xs font-semibold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-full capitalize">
              {garment.garmentType}
            </span>
          ) : (
            <span className="text-xs text-gray-400 italic">
              {garment.classificationError ? '⚠ Failed' : 'Processing…'}
            </span>
          )}
          {garment.style && (
            <span className="text-xs text-gray-500 truncate capitalize">{garment.style}</span>
          )}
        </div>
        {garment.colorPalette.length > 0 && <ColorChips colors={garment.colorPalette} />}
      </div>
    </div>
  )
}
