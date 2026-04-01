import { useEffect, useState, useCallback } from 'react'
import { listGarments } from '@/api/client'
import type { GarmentListItem, SearchParams } from '@/types/garment'

export function useGarments(params: SearchParams, refreshKey: number) {
  const [items, setItems] = useState<GarmentListItem[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await listGarments({ ...params, limit: 100 })
      setItems(result.items)
      setTotal(result.total)
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }, [JSON.stringify(params)]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    load()
  }, [load, refreshKey])

  return { items, total, loading, error }
}
