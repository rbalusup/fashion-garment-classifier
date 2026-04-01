import type {
  Annotation,
  FilterOptions,
  GarmentOut,
  PaginatedGarments,
  SearchParams,
} from '@/types/garment'

const BASE = '/api'

function toSnakeQuery(params: SearchParams): string {
  const p = new URLSearchParams()
  if (params.q) p.set('q', params.q)
  if (params.garment_type) p.set('garment_type', params.garment_type)
  if (params.style) p.set('style', params.style)
  if (params.material) p.set('material', params.material)
  if (params.color) p.set('color', params.color)
  if (params.pattern) p.set('pattern', params.pattern)
  if (params.season) p.set('season', params.season)
  if (params.occasion) p.set('occasion', params.occasion)
  if (params.continent) p.set('continent', params.continent)
  if (params.country) p.set('country', params.country)
  if (params.city) p.set('city', params.city)
  if (params.year != null) p.set('year', String(params.year))
  if (params.month != null) p.set('month', String(params.month))
  if (params.designer) p.set('designer', params.designer)
  if (params.skip != null) p.set('skip', String(params.skip))
  if (params.limit != null) p.set('limit', String(params.limit))
  const qs = p.toString()
  return qs ? `?${qs}` : ''
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API ${res.status}: ${text}`)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

// Garments
export async function listGarments(params: SearchParams = {}): Promise<PaginatedGarments> {
  return apiFetch(`${BASE}/garments${toSnakeQuery(params)}`)
}

export async function getGarment(id: number): Promise<GarmentOut> {
  return apiFetch(`${BASE}/garments/${id}`)
}

export async function uploadGarment(
  file: File,
  meta: { continent?: string; country?: string; city?: string; designer?: string; year?: number }
): Promise<GarmentOut> {
  const form = new FormData()
  form.append('file', file)
  if (meta.continent) form.append('continent', meta.continent)
  if (meta.country) form.append('country', meta.country)
  if (meta.city) form.append('city', meta.city)
  if (meta.designer) form.append('designer', meta.designer)
  if (meta.year) form.append('year', String(meta.year))
  return apiFetch(`${BASE}/upload`, { method: 'POST', body: form })
}

export async function updateGarment(
  id: number,
  update: { designer?: string; year?: number; month?: number }
): Promise<GarmentOut> {
  return apiFetch(`${BASE}/garments/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(update),
  })
}

export async function deleteGarment(id: number): Promise<void> {
  return apiFetch(`${BASE}/garments/${id}`, { method: 'DELETE' })
}

export async function reclassifyGarment(id: number): Promise<GarmentOut> {
  return apiFetch(`${BASE}/garments/${id}/reclassify`, { method: 'POST' })
}

// Annotations
export async function listAnnotations(garmentId: number): Promise<Annotation[]> {
  return apiFetch(`${BASE}/annotations/${garmentId}`)
}

export async function createAnnotation(
  garmentId: number,
  tags: string[],
  notes: string
): Promise<Annotation> {
  return apiFetch(`${BASE}/annotations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ garment_id: garmentId, tags, notes }),
  })
}

export async function deleteAnnotation(id: number): Promise<void> {
  return apiFetch(`${BASE}/annotations/${id}`, { method: 'DELETE' })
}

// Filters
export async function getFilterOptions(): Promise<FilterOptions> {
  return apiFetch(`${BASE}/filters/options`)
}
