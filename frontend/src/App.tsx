import { useEffect, useMemo, useState, type ReactNode } from 'react'
import {
  ArrowDownUp,
  CalendarRange,
  ChevronRight,
  Grid2X2,
  ListFilter,
  Menu,
  Search,
  Sparkles,
  X,
} from 'lucide-react'

import { AgendaView } from './components/AgendaView'
import { BrandMark } from './components/BrandMark'
import { EventCard } from './components/EventCard'
import { EventDetail } from './components/EventDetail'
import { FilterPanel } from './components/FilterPanel'
import { ConnectionState, EmptyState, EventSkeletons } from './components/States'
import { useEvents } from './hooks/useEvents'
import {
  categoryLabel,
  filterAndSortEvents,
  uniqueValues,
} from './lib/events'
import {
  DEFAULT_FILTERS,
  type EventFilters,
  type SortOrder,
  type TechEvent,
  type ViewMode,
} from './types/event'

function selectedSlugFromUrl(): string | null {
  return new URLSearchParams(window.location.search).get('event')
}

export default function App() {
  const { events, loading, error, refresh } = useEvents()
  const [filters, setFilters] = useState<EventFilters>(DEFAULT_FILTERS)
  const [sortOrder, setSortOrder] = useState<SortOrder>('ascending')
  const [viewMode, setViewMode] = useState<ViewMode>('cards')
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [selectedSlug, setSelectedSlug] = useState<string | null>(selectedSlugFromUrl)

  useEffect(() => {
    const handlePopState = () => setSelectedSlug(selectedSlugFromUrl())
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  const categories = useMemo(
    () => uniqueValues(events, (event) => event.category),
    [events],
  )
  const filteredEvents = useMemo(
    () => filterAndSortEvents(events, filters, sortOrder),
    [events, filters, sortOrder],
  )
  const selectedEvent = events.find((event) => event.slug === selectedSlug) ?? null
  const activeFilterCount = Object.entries(filters).filter(([key, value]) => {
    if (key === 'search') return value !== ''
    if (key === 'freeOnly') return value === true
    return value !== 'all'
  }).length
  const organizations = new Set(events.map((event) => event.organization).filter(Boolean)).size
  const freeEvents = events.filter((event) => event.is_free === true).length

  function selectEvent(event: TechEvent) {
    const params = new URLSearchParams(window.location.search)
    params.set('event', event.slug)
    window.history.pushState({}, '', `${window.location.pathname}?${params.toString()}`)
    setSelectedSlug(event.slug)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function closeEvent() {
    window.history.pushState({}, '', window.location.pathname)
    setSelectedSlug(null)
    window.scrollTo({ top: 0 })
  }

  if (selectedEvent) return <EventDetail event={selectedEvent} onBack={closeEvent} />

  return (
    <div className="min-h-screen bg-[#f3f6f1] text-slate-900">
      <header className="relative overflow-hidden bg-emerald-950 text-white">
        <div className="absolute inset-0 hero-grid opacity-35" aria-hidden="true" />
        <div className="absolute -right-28 top-12 size-96 rounded-full border border-lime-300/10" />
        <div className="absolute -right-10 top-32 size-56 rounded-full bg-lime-300/5 blur-3xl" />

        <nav className="relative mx-auto flex max-w-7xl items-center justify-between px-5 py-5 sm:px-8" aria-label="Navegación principal">
          <BrandMark />
          <div className="hidden items-center gap-7 text-sm font-semibold text-emerald-50/70 md:flex">
            <a href="#eventos" className="transition hover:text-white">Eventos</a>
            <a href="#categorias" className="transition hover:text-white">Categorías</a>
            <a href="#como-funciona" className="transition hover:text-white">Cómo funciona</a>
            <span className="flex items-center gap-2 rounded-full border border-emerald-100/15 bg-white/5 px-3 py-2 text-xs text-emerald-100">
              <span className="size-2 animate-pulse rounded-full bg-lime-300" /> Actualización automática
            </span>
          </div>
          <button type="button" className="grid size-10 place-items-center rounded-full border border-white/15 md:hidden" onClick={() => setMobileMenuOpen(!mobileMenuOpen)} aria-label="Abrir menú">
            {mobileMenuOpen ? <X className="size-5" /> : <Menu className="size-5" />}
          </button>
        </nav>

        {mobileMenuOpen && (
          <div className="relative mx-5 mb-4 grid gap-2 rounded-2xl border border-white/10 bg-white/5 p-3 text-sm font-semibold backdrop-blur md:hidden">
            <a href="#eventos" onClick={() => setMobileMenuOpen(false)} className="rounded-xl px-3 py-2 hover:bg-white/10">Eventos</a>
            <a href="#categorias" onClick={() => setMobileMenuOpen(false)} className="rounded-xl px-3 py-2 hover:bg-white/10">Categorías</a>
            <a href="#como-funciona" onClick={() => setMobileMenuOpen(false)} className="rounded-xl px-3 py-2 hover:bg-white/10">Cómo funciona</a>
          </div>
        )}

        <section className="relative mx-auto max-w-7xl px-5 pb-20 pt-12 sm:px-8 sm:pb-24 sm:pt-16">
          <div className="max-w-4xl">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-lime-300/25 bg-lime-300/10 px-3 py-1.5 text-xs font-bold text-lime-200">
              <Sparkles className="size-3.5" /> Tu radar de tecnología en Perú
            </div>
            <h1 className="text-balance text-4xl font-black leading-[0.98] tracking-[-0.055em] sm:text-6xl lg:text-7xl">
              El próximo evento que puede <span className="text-lime-300">cambiar tu ruta</span> está aquí.
            </h1>
            <p className="mt-6 max-w-2xl text-base leading-7 text-emerald-50/65 sm:text-lg">
              Workshops, meetups, conferencias y hackathons de las mejores comunidades tech, reunidos y actualizados en un solo lugar.
            </p>

            <div className="mt-9 flex max-w-3xl items-center rounded-2xl border border-white/15 bg-white p-2 shadow-[0_18px_55px_rgba(0,0,0,0.2)]">
              <Search className="ml-3 size-5 shrink-0 text-emerald-700" aria-hidden="true" />
              <label htmlFor="event-search" className="sr-only">Buscar eventos</label>
              <input id="event-search" type="search" value={filters.search} onChange={(event) => setFilters({ ...filters, search: event.target.value })} placeholder="Busca IA, Python, AWS, hackathons..." className="min-w-0 flex-1 bg-transparent px-3 py-3 text-sm font-medium text-emerald-950 outline-none placeholder:text-slate-400 sm:text-base" />
              <a href="#eventos" className="hidden rounded-xl bg-lime-300 px-5 py-3 text-sm font-extrabold text-emerald-950 transition hover:bg-lime-200 sm:block">Explorar</a>
            </div>
          </div>

          <div className="mt-12 flex flex-wrap gap-x-9 gap-y-4 border-t border-white/10 pt-7">
            <Stat value={loading ? '—' : String(events.length)} label="eventos próximos" />
            <Stat value={loading ? '—' : String(organizations)} label="organizadores" />
            <Stat value={loading ? '—' : String(freeEvents)} label="confirmados gratis" />
          </div>
        </section>
      </header>

      <main id="eventos" className="mx-auto max-w-7xl px-5 py-10 sm:px-8 sm:py-14">
        <section id="categorias" aria-labelledby="category-heading">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-emerald-700">Explora por tema</p>
              <h2 id="category-heading" className="mt-2 text-2xl font-black tracking-[-0.04em] text-emerald-950 sm:text-3xl">¿Qué quieres aprender ahora?</h2>
            </div>
            {filters.category !== 'all' && <button type="button" onClick={() => setFilters({ ...filters, category: 'all' })} className="hidden text-sm font-bold text-emerald-700 hover:text-emerald-950 sm:block">Ver todas</button>}
          </div>
          <div className="mt-6 flex gap-2 overflow-x-auto pb-3 scrollbar-none">
            <button type="button" onClick={() => setFilters({ ...filters, category: 'all' })} className={`shrink-0 rounded-full border px-4 py-2.5 text-sm font-bold transition ${filters.category === 'all' ? 'border-emerald-950 bg-emerald-950 text-white' : 'border-slate-200 bg-white text-slate-600 hover:border-emerald-300'}`}>Todo</button>
            {categories.map((category) => (
              <button type="button" key={category} onClick={() => setFilters({ ...filters, category })} className={`shrink-0 rounded-full border px-4 py-2.5 text-sm font-bold transition ${filters.category === category ? 'border-emerald-950 bg-emerald-950 text-white' : 'border-slate-200 bg-white text-slate-600 hover:border-emerald-300'}`}>{categoryLabel(category)}</button>
            ))}
          </div>
        </section>

        <div className="mt-8 grid gap-6 lg:grid-cols-[260px_1fr]">
          <FilterPanel events={events} filters={filters} onChange={setFilters} activeCount={activeFilterCount} mobileOpen={mobileFiltersOpen} onCloseMobile={() => setMobileFiltersOpen(false)} />

          <section aria-live="polite">
            <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm font-bold text-emerald-950">{loading ? 'Buscando eventos...' : `${filteredEvents.length} ${filteredEvents.length === 1 ? 'evento encontrado' : 'eventos encontrados'}`}</p>
                <p className="mt-1 text-xs text-slate-400">Ordenados por fecha y hora local</p>
              </div>
              <div className="flex items-center gap-2">
                <button type="button" onClick={() => setMobileFiltersOpen(true)} className="relative flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-xs font-bold text-emerald-950 lg:hidden">
                  <ListFilter className="size-4" /> Filtros
                  {activeFilterCount > 0 && <span className="grid size-5 place-items-center rounded-full bg-lime-300 text-[10px]">{activeFilterCount}</span>}
                </button>
                <button type="button" onClick={() => setSortOrder(sortOrder === 'ascending' ? 'descending' : 'ascending')} className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-xs font-bold text-emerald-950" title="Cambiar orden">
                  <ArrowDownUp className="size-4" /> {sortOrder === 'ascending' ? 'Próximos' : 'Más lejanos'}
                </button>
                <div className="hidden rounded-xl border border-slate-200 bg-white p-1 sm:flex">
                  <ViewButton active={viewMode === 'cards'} label="Tarjetas" onClick={() => setViewMode('cards')} icon={<Grid2X2 />} />
                  <ViewButton active={viewMode === 'agenda'} label="Agenda" onClick={() => setViewMode('agenda')} icon={<CalendarRange />} />
                </div>
              </div>
            </div>

            {loading && <EventSkeletons />}
            {!loading && error && <ConnectionState error={error} onRetry={() => void refresh()} />}
            {!loading && !error && filteredEvents.length === 0 && <EmptyState onReset={() => setFilters(DEFAULT_FILTERS)} />}
            {!loading && !error && filteredEvents.length > 0 && viewMode === 'cards' && (
              <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
                {filteredEvents.map((event) => <EventCard key={event.id} event={event} onSelect={selectEvent} />)}
              </div>
            )}
            {!loading && !error && filteredEvents.length > 0 && viewMode === 'agenda' && <AgendaView events={filteredEvents} onSelect={selectEvent} />}
          </section>
        </div>

        <section id="como-funciona" className="mt-20 overflow-hidden rounded-[1.8rem] bg-emerald-950 px-6 py-10 text-white sm:px-10 sm:py-12">
          <div className="grid gap-8 lg:grid-cols-[1fr_1.4fr] lg:items-end">
            <div>
              <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-lime-300">Siempre al día</p>
              <h2 className="mt-3 text-3xl font-black tracking-[-0.045em] sm:text-4xl">Menos pestañas. Más comunidad.</h2>
              <p className="mt-4 max-w-md text-sm leading-6 text-emerald-50/60">Reunimos fuentes oficiales, normalizamos sus datos y eliminamos duplicados automáticamente.</p>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              {['Recopilamos cada 6 horas', 'Clasificamos por tema', 'Te llevamos a la fuente'].map((item, index) => (
                <div key={item} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <span className="text-xs font-black text-lime-300">0{index + 1}</span>
                  <p className="mt-7 flex items-end justify-between gap-3 text-sm font-bold">{item}<ChevronRight className="size-4 shrink-0 text-emerald-300" /></p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>

      <footer className="mt-10 border-t border-emerald-950/8 bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-5 py-7 text-xs text-slate-400 sm:flex-row sm:items-center sm:justify-between sm:px-8">
          <p><strong className="text-emerald-950">TechEvents Perú</strong> · Hecho para la comunidad tecnológica.</p>
          <p>Los detalles finales pertenecen a cada organizador.</p>
        </div>
      </footer>
    </div>
  )
}

function Stat({ value, label }: { value: string; label: string }) {
  return <div className="flex items-baseline gap-2"><strong className="text-2xl font-black text-lime-300">{value}</strong><span className="text-xs font-semibold text-emerald-50/50">{label}</span></div>
}

function ViewButton({ active, label, onClick, icon }: { active: boolean; label: string; onClick: () => void; icon: ReactNode }) {
  return <button type="button" onClick={onClick} className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-bold transition [&>svg]:size-3.5 ${active ? 'bg-emerald-950 text-white' : 'text-slate-500 hover:bg-slate-100'}`} aria-pressed={active}>{icon}{label}</button>
}

