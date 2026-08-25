export type EventModality = 'in_person' | 'virtual' | 'hybrid'

export interface TechEvent {
  id: string
  title: string
  slug: string
  description: string | null
  organization: string | null
  category: string
  subcategory: string | null
  tags: string[]
  event_type: string | null
  start_date: string
  end_date: string | null
  timezone: string
  modality: EventModality
  venue: string | null
  city: string | null
  country: string | null
  is_free: boolean | null
  price: number | null
  currency: string | null
  registration_url: string | null
  source_url: string
  image_url: string | null
  source: string
  status: string
}

export type DateRange = 'all' | 'today' | 'week' | 'month'
export type SortOrder = 'ascending' | 'descending'
export type ViewMode = 'cards' | 'agenda'

export interface EventFilters {
  search: string
  category: string
  modality: EventModality | 'all'
  city: string
  organization: string
  eventType: string
  source: string
  dateRange: DateRange
  freeOnly: boolean
}

export const DEFAULT_FILTERS: EventFilters = {
  search: '',
  category: 'all',
  modality: 'all',
  city: 'all',
  organization: 'all',
  eventType: 'all',
  source: 'all',
  dateRange: 'all',
  freeOnly: false,
}

