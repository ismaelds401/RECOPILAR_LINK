import { describe, expect, it } from 'vitest'

import { DEFAULT_FILTERS, type TechEvent } from '../types/event'
import { filterAndSortEvents, normalizeForSearch } from './events'

const baseEvent: TechEvent = {
  id: '1',
  title: 'Introducción a Inteligencia Artificial',
  slug: 'introduccion-ia',
  description: 'Aprende modelos con Python',
  organization: 'Comunidad Perú Tech',
  category: 'Artificial Intelligence',
  subcategory: null,
  tags: ['IA', 'Python'],
  event_type: 'Meetup',
  start_date: '2026-08-26T15:00:00-05:00',
  end_date: null,
  timezone: 'America/Lima',
  modality: 'in_person',
  venue: 'Centro de Convenciones',
  city: 'Lima',
  country: 'Perú',
  is_free: true,
  price: null,
  currency: null,
  registration_url: 'https://example.com/register',
  source_url: 'https://example.com/event',
  image_url: null,
  source: 'GDG',
  status: 'published',
}

const virtualEvent: TechEvent = {
  ...baseEvent,
  id: '2',
  title: 'Cloud para equipos',
  slug: 'cloud-equipos',
  category: 'Cloud',
  start_date: '2026-08-30T18:00:00-05:00',
  modality: 'virtual',
  city: null,
  is_free: false,
  source: 'AWS',
}

describe('event helpers', () => {
  it('normalizes accents and casing for search', () => {
    expect(normalizeForSearch('Tecnología en PERÚ')).toBe('tecnologia en peru')
  })

  it('searches across event fields without accents', () => {
    const result = filterAndSortEvents(
      [virtualEvent, baseEvent],
      { ...DEFAULT_FILTERS, search: 'introduccion peru' },
      'ascending',
      new Date('2026-08-25T12:00:00-05:00'),
    )

    expect(result.map((event) => event.id)).toEqual(['1'])
  })

  it('combines filters and preserves chronological order', () => {
    const result = filterAndSortEvents(
      [virtualEvent, baseEvent],
      {
        ...DEFAULT_FILTERS,
        category: 'Artificial Intelligence',
        modality: 'in_person',
        city: 'Lima',
        freeOnly: true,
        dateRange: 'week',
      },
      'ascending',
      new Date('2026-08-25T12:00:00-05:00'),
    )

    expect(result).toEqual([baseEvent])
  })

  it('sorts newest dates first when requested', () => {
    const result = filterAndSortEvents(
      [baseEvent, virtualEvent],
      DEFAULT_FILTERS,
      'descending',
    )

    expect(result.map((event) => event.id)).toEqual(['2', '1'])
  })
})

