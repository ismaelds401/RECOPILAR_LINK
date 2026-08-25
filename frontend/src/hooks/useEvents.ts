import { useCallback, useEffect, useState } from 'react'

import { isSupabaseConfigured, supabase } from '../lib/supabase'
import type { TechEvent } from '../types/event'

interface EventsState {
  events: TechEvent[]
  loading: boolean
  error: string | null
  refresh: () => Promise<void>
}

export function useEvents(): EventsState {
  const [events, setEvents] = useState<TechEvent[]>([])
  const [loading, setLoading] = useState(isSupabaseConfigured)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    if (!supabase) {
      setLoading(false)
      setError('Falta configurar la conexión pública con Supabase.')
      return
    }
    setLoading(true)
    setError(null)
    const { data, error: queryError } = await supabase
      .from('events')
      .select(
        'id,title,slug,description,organization,category,subcategory,tags,event_type,start_date,end_date,timezone,modality,venue,city,country,is_free,price,currency,registration_url,source_url,image_url,source,status',
      )
      .eq('status', 'published')
      .gte('start_date', new Date().toISOString())
      .order('start_date', { ascending: true })
      .limit(500)

    if (queryError) {
      setError(`No se pudieron cargar los eventos: ${queryError.message}`)
      setEvents([])
    } else {
      setEvents((data ?? []) as TechEvent[])
    }
    setLoading(false)
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  return { events, loading, error, refresh }
}

