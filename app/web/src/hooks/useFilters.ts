import { useEffect, useState } from 'react'
import { getFilterOptions } from '@/api/client'
import type { FilterOptions } from '@/types/garment'

export function useFilters() {
  const [options, setOptions] = useState<FilterOptions | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getFilterOptions()
      .then(setOptions)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  return { options, loading }
}
