import { useCallback, useEffect, useState } from 'react'
import { createAnnotation, deleteAnnotation, listAnnotations } from '@/api/client'
import type { Annotation } from '@/types/garment'

export function useAnnotations(garmentId: number) {
  const [annotations, setAnnotations] = useState<Annotation[]>([])
  const [loading, setLoading] = useState(true)

  const reload = useCallback(async () => {
    setLoading(true)
    try {
      const data = await listAnnotations(garmentId)
      setAnnotations(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }, [garmentId])

  useEffect(() => { reload() }, [reload])

  const add = useCallback(
    async (tags: string[], notes: string) => {
      await createAnnotation(garmentId, tags, notes)
      reload()
    },
    [garmentId, reload]
  )

  const remove = useCallback(
    async (id: number) => {
      await deleteAnnotation(id)
      reload()
    },
    [reload]
  )

  return { annotations, loading, add, remove, reload }
}
