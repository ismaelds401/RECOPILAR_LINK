import type {
  EventFilters,
  EventModality,
  SortOrder,
  TechEvent,
} from '../types/event'

export const modalityLabels: Record<EventModality, string> = {
  in_person: 'Presencial',
  virtual: 'Virtual',
  hybrid: 'Híbrido',
}

const categoryStyles: Record<string, string> = {
  'Artificial Intelligence': 'bg-violet-100 text-violet-800',
  Cloud: 'bg-sky-100 text-sky-800',
  Data: 'bg-blue-100 text-blue-800',
  Cybersecurity: 'bg-red-100 text-red-800',
  DevOps: 'bg-cyan-100 text-cyan-800',
  Programming: 'bg-amber-100 text-amber-900',
  'Web Development': 'bg-fuchsia-100 text-fuchsia-800',
  Mobile: 'bg-pink-100 text-pink-800',
  Blockchain: 'bg-orange-100 text-orange-800',
  Networking: 'bg-teal-100 text-teal-800',
  IoT: 'bg-lime-100 text-lime-900',
  Entrepreneurship: 'bg-yellow-100 text-yellow-900',
  Technology: 'bg-emerald-100 text-emerald-800',
  Other: 'bg-slate-100 text-slate-700',
}

const categoryLabels: Record<string, string> = {
  'Artificial Intelligence': 'Inteligencia Artificial',
  Cybersecurity: 'Ciberseguridad',
  Programming: 'Programación',
  'Web Development': 'Desarrollo web',
  Mobile: 'Mobile',
  Networking: 'Redes',
  Entrepreneurship: 'Emprendimiento',
  Technology: 'Tecnología',
  Other: 'Otros',
}

export function categoryLabel(category: string): string {
  return categoryLabels[category] ?? category
}

export function categoryClass(category: string): string {
  return categoryStyles[category] ?? categoryStyles.Other
}

export function normalizeForSearch(value: string | null | undefined): string {
  return (value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLocaleLowerCase('es')
}

export function filterAndSortEvents(
  events: TechEvent[],
  filters: EventFilters,
  sortOrder: SortOrder,
  now = new Date(),
): TechEvent[] {
  const query = normalizeForSearch(filters.search.trim())
  const todayStart = new Date(now)
  todayStart.setHours(0, 0, 0, 0)
  const todayEnd = new Date(todayStart)
  todayEnd.setDate(todayEnd.getDate() + 1)
  const weekEnd = new Date(todayStart)
  weekEnd.setDate(weekEnd.getDate() + 7)
  const monthEnd = new Date(todayStart)
  monthEnd.setDate(monthEnd.getDate() + 30)

  return events
    .filter((event) => {
      const start = new Date(event.start_date)
      if (query) {
        const queryTerms = query.split(/\s+/).filter(Boolean)
        const haystack = normalizeForSearch(
          [
            event.title,
            event.description,
            event.organization,
            event.category,
            event.city,
            ...event.tags,
          ]
            .filter(Boolean)
            .join(' '),
        )
        if (!queryTerms.every((term) => haystack.includes(term))) return false
      }
      if (filters.category !== 'all' && event.category !== filters.category)
        return false
      if (filters.modality !== 'all' && event.modality !== filters.modality)
        return false
      if (filters.city !== 'all' && (event.city ?? '') !== filters.city)
        return false
      if (
        filters.organization !== 'all' &&
        (event.organization ?? '') !== filters.organization
      )
        return false
      if (
        filters.eventType !== 'all' &&
        (event.event_type ?? '') !== filters.eventType
      )
        return false
      if (filters.source !== 'all' && event.source !== filters.source) return false
      if (filters.freeOnly && event.is_free !== true) return false
      if (filters.dateRange === 'today' && !(start >= todayStart && start < todayEnd))
        return false
      if (filters.dateRange === 'week' && !(start >= todayStart && start < weekEnd))
        return false
      if (filters.dateRange === 'month' && !(start >= todayStart && start < monthEnd))
        return false
      return true
    })
    .sort((first, second) => {
      const difference =
        new Date(first.start_date).getTime() - new Date(second.start_date).getTime()
      return sortOrder === 'ascending' ? difference : -difference
    })
}

export function uniqueValues(
  events: TechEvent[],
  selector: (event: TechEvent) => string | null,
): string[] {
  return [...new Set(events.map(selector).filter((value): value is string => Boolean(value)))].sort(
    (first, second) => first.localeCompare(second, 'es'),
  )
}

export function formatEventDate(value: string): string {
  return new Intl.DateTimeFormat('es-PE', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
  }).format(new Date(value))
}

export function formatEventTime(value: string): string {
  return new Intl.DateTimeFormat('es-PE', {
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(value))
}

export function formatFullDate(value: string): string {
  return new Intl.DateTimeFormat('es-PE', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(value))
}

export function groupEventsByDay(events: TechEvent[]): [string, TechEvent[]][] {
  const formatter = new Intl.DateTimeFormat('en-CA', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
  const groups = new Map<string, TechEvent[]>()
  for (const event of events) {
    const key = formatter.format(new Date(event.start_date))
    groups.set(key, [...(groups.get(key) ?? []), event])
  }
  return [...groups.entries()]
}

