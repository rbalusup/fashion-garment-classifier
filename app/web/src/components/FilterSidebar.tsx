import { useCallback, useState } from 'react'
import type { SearchParams } from '@/types/garment'
import { useFilters } from '@/hooks/useFilters'

interface Props {
  onChange: (filters: Partial<SearchParams>) => void
}

const FILTER_GROUPS: { key: keyof SearchParams; label: string }[] = [
  { key: 'garment_type', label: 'Garment Type' },
  { key: 'style', label: 'Style' },
  { key: 'material', label: 'Material' },
  { key: 'color', label: 'Color' },
  { key: 'pattern', label: 'Pattern' },
  { key: 'season', label: 'Season' },
  { key: 'occasion', label: 'Occasion' },
  { key: 'continent', label: 'Continent' },
  { key: 'country', label: 'Country' },
  { key: 'city', label: 'City' },
  { key: 'designer', label: 'Designer' },
]

const FILTER_OPTIONS_MAP: Record<string, keyof import('@/types/garment').FilterOptions> = {
  garment_type: 'garment_type',
  style: 'style',
  material: 'material',
  color: 'color',
  pattern: 'pattern',
  season: 'season',
  occasion: 'occasion',
  continent: 'location_continent',
  country: 'location_country',
  city: 'location_city',
  designer: 'designer',
}

export function FilterSidebar({ onChange }: Props) {
  const { options, loading } = useFilters()
  const [active, setActive] = useState<Partial<SearchParams>>({})
  const [expanded, setExpanded] = useState<Set<string>>(new Set(['garment_type', 'style']))

  const toggle = useCallback(
    (key: keyof SearchParams, value: string) => {
      setActive(prev => {
        const current = prev[key] as string | undefined
        const next = current === value ? undefined : value
        const updated = { ...prev, [key]: next }
        onChange(updated)
        return updated
      })
    },
    [onChange]
  )

  const toggleExpand = (key: string) => {
    setExpanded(prev => {
      const next = new Set(prev)
      next.has(key) ? next.delete(key) : next.add(key)
      return next
    })
  }

  if (loading) {
    return (
      <aside className="w-56 shrink-0 border-r bg-white p-4 sticky top-14 h-[calc(100vh-3.5rem)] overflow-y-auto">
        <div className="text-sm text-gray-400 animate-pulse">Loading filters…</div>
      </aside>
    )
  }

  return (
    <aside className="w-56 shrink-0 border-r bg-white p-4 sticky top-14 h-[calc(100vh-3.5rem)] overflow-y-auto space-y-3">
      <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Filters</h2>
      {FILTER_GROUPS.map(({ key, label }) => {
        const optKey = FILTER_OPTIONS_MAP[key as string]
        const values = options ? (options[optKey] as string[]) : []
        if (!values || values.length === 0) return null
        const isExpanded = expanded.has(key as string)
        return (
          <div key={key as string}>
            <button
              className="w-full flex justify-between items-center text-sm font-medium text-gray-700 hover:text-gray-900"
              onClick={() => toggleExpand(key as string)}
            >
              <span>{label}</span>
              <span className="text-gray-400">{isExpanded ? '▲' : '▼'}</span>
            </button>
            {isExpanded && (
              <ul className="mt-1 space-y-0.5 pl-1">
                {values.map(v => (
                  <li key={v}>
                    <label className="flex items-center gap-2 cursor-pointer group">
                      <input
                        type="checkbox"
                        className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                        checked={(active[key] as string) === v}
                        onChange={() => toggle(key, v)}
                      />
                      <span className="text-xs text-gray-600 group-hover:text-gray-900 capitalize">
                        {v}
                      </span>
                    </label>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )
      })}
    </aside>
  )
}
