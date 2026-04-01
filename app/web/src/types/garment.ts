export interface LocationContext {
  continent: string | null
  country: string | null
  city: string | null
}

export interface Annotation {
  id: number
  garmentId: number
  createdAt: string
  updatedAt: string
  tags: string[]
  notes: string | null
  source: 'designer'
}

export interface GarmentOut {
  id: number
  uuid: string
  originalFilename: string
  imagePath: string
  uploadedAt: string
  classifiedAt: string | null
  description: string | null
  garmentType: string | null
  style: string | null
  material: string | null
  colorPalette: string[]
  pattern: string | null
  season: string | null
  occasion: string | null
  consumerProfile: string | null
  trendNotes: string | null
  locationContinent: string | null
  locationCountry: string | null
  locationCity: string | null
  designer: string | null
  year: number | null
  month: number | null
  classificationError: string | null
  annotations: Annotation[]
}

export interface GarmentListItem {
  id: number
  uuid: string
  imagePath: string
  garmentType: string | null
  style: string | null
  colorPalette: string[]
  classificationError: string | null
}

export interface PaginatedGarments {
  items: GarmentListItem[]
  total: number
  skip: number
  limit: number
}

export interface FilterOptions {
  garment_type: string[]
  style: string[]
  material: string[]
  color: string[]
  pattern: string[]
  season: string[]
  occasion: string[]
  location_continent: string[]
  location_country: string[]
  location_city: string[]
  designer: string[]
  year: number[]
}

export interface SearchParams {
  q?: string
  garment_type?: string
  style?: string
  material?: string
  color?: string
  pattern?: string
  season?: string
  occasion?: string
  continent?: string
  country?: string
  city?: string
  year?: number
  month?: number
  designer?: string
  skip?: number
  limit?: number
}
