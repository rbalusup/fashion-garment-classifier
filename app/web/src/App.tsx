import { useState, useCallback } from 'react'
import type { GarmentOut, SearchParams } from '@/types/garment'
import { SearchBar } from '@/components/SearchBar'
import { FilterSidebar } from '@/components/FilterSidebar'
import { GarmentGrid } from '@/components/GarmentGrid'
import { UploadModal } from '@/components/UploadModal'
import { DetailModal } from '@/components/DetailModal'

export default function App() {
  const [searchParams, setSearchParams] = useState<SearchParams>({})
  const [uploadOpen, setUploadOpen] = useState(false)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  const refresh = useCallback(() => setRefreshKey(k => k + 1), [])

  const handleSearch = useCallback((q: string) => {
    setSearchParams(prev => ({ ...prev, q: q || undefined }))
  }, [])

  const handleFilterChange = useCallback((filters: Partial<SearchParams>) => {
    setSearchParams(prev => ({ ...prev, ...filters, q: prev.q }))
  }, [])

  const handleUploadSuccess = useCallback((_garment: GarmentOut) => {
    setUploadOpen(false)
    refresh()
  }, [refresh])

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="sticky top-0 z-30 bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-4 shadow-sm">
        <h1 className="font-bold text-xl text-gray-900 shrink-0">🧵 Fashion Archive</h1>
        <div className="flex-1 max-w-xl">
          <SearchBar onSearch={handleSearch} />
        </div>
        <button
          onClick={() => setUploadOpen(true)}
          className="shrink-0 bg-indigo-600 hover:bg-indigo-700 text-white font-medium px-4 py-2 rounded-lg text-sm transition-colors"
        >
          + Upload
        </button>
      </header>

      {/* Body */}
      <div className="flex">
        <FilterSidebar onChange={handleFilterChange} />
        <main className="flex-1 p-6 min-w-0">
          <GarmentGrid
            searchParams={searchParams}
            refreshKey={refreshKey}
            onSelect={id => setSelectedId(id)}
          />
        </main>
      </div>

      {/* Modals */}
      {uploadOpen && (
        <UploadModal
          onClose={() => setUploadOpen(false)}
          onSuccess={handleUploadSuccess}
        />
      )}
      {selectedId !== null && (
        <DetailModal
          garmentId={selectedId}
          onClose={() => setSelectedId(null)}
          onAnnotationChange={refresh}
        />
      )}
    </div>
  )
}
