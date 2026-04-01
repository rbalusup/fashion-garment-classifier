import type { SearchParams } from '@/types/garment'
import { useGarments } from '@/hooks/useGarments'
import { GarmentCard } from './GarmentCard'

interface Props {
  searchParams: SearchParams
  refreshKey: number
  onSelect: (id: number) => void
}

export function GarmentGrid({ searchParams, refreshKey, onSelect }: Props) {
  const { items, total, loading, error } = useGarments(searchParams, refreshKey)

  if (loading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
        {Array.from({ length: 10 }).map((_, i) => (
          <div key={i} className="aspect-[3/4] rounded-xl bg-gray-200 animate-pulse" />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-20 text-red-500">
        <p className="text-4xl mb-2">⚠</p>
        <p className="font-medium">Failed to load garments</p>
        <p className="text-sm text-gray-400 mt-1">{error}</p>
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <div className="text-center py-20 text-gray-400">
        <p className="text-5xl mb-3">👗</p>
        <p className="font-medium text-gray-600">No garments yet</p>
        <p className="text-sm mt-1">Upload your first photo to get started</p>
      </div>
    )
  }

  return (
    <>
      <p className="text-sm text-gray-500 mb-4">
        {total} garment{total !== 1 ? 's' : ''}
      </p>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
        {items.map(g => (
          <GarmentCard key={g.id} garment={g} onClick={() => onSelect(g.id)} />
        ))}
      </div>
    </>
  )
}
