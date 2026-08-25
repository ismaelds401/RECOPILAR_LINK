import { RotateCcw, SlidersHorizontal, X } from 'lucide-react'

import { modalityLabels } from '../lib/events'
import { DEFAULT_FILTERS, type EventFilters, type EventModality, type TechEvent } from '../types/event'
import { uniqueValues } from '../lib/events'

interface FilterPanelProps {
  events: TechEvent[]
  filters: EventFilters
  onChange: (filters: EventFilters) => void
  activeCount: number
  mobileOpen: boolean
  onCloseMobile: () => void
}

function SelectField({
  id,
  label,
  value,
  values,
  onChange,
}: {
  id: string
  label: string
  value: string
  values: string[]
  onChange: (value: string) => void
}) {
  return (
    <label htmlFor={id} className="grid gap-2 text-xs font-extrabold uppercase tracking-[0.12em] text-slate-500">
      {label}
      <select
        id={id}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="w-full rounded-xl border border-slate-200 bg-white px-3 py-3 text-sm font-semibold normal-case tracking-normal text-emerald-950 outline-none transition focus:border-emerald-600 focus:ring-2 focus:ring-emerald-100"
      >
        <option value="all">Todos</option>
        {values.map((option) => (
          <option value={option} key={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  )
}

export function FilterPanel({
  events,
  filters,
  onChange,
  activeCount,
  mobileOpen,
  onCloseMobile,
}: FilterPanelProps) {
  const cities = uniqueValues(events, (event) => event.city)
  const organizations = uniqueValues(events, (event) => event.organization)
  const eventTypes = uniqueValues(events, (event) => event.event_type)
  const sources = uniqueValues(events, (event) => event.source)

  const content = (
    <div className="grid gap-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="size-4 text-emerald-700" />
          <h2 className="font-extrabold text-emerald-950">Afinar resultados</h2>
          {activeCount > 0 && (
            <span className="grid size-5 place-items-center rounded-full bg-emerald-950 text-[10px] font-bold text-white">
              {activeCount}
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={() => onChange(DEFAULT_FILTERS)}
          className="flex items-center gap-1 text-xs font-bold text-emerald-700 hover:text-emerald-950"
        >
          <RotateCcw className="size-3.5" />
          Limpiar
        </button>
      </div>

      <div className="grid grid-cols-2 gap-2">
        {(['all', 'today', 'week', 'month'] as const).map((range) => {
          const labels = { all: 'Cualquier fecha', today: 'Hoy', week: '7 días', month: '30 días' }
          return (
            <button
              type="button"
              key={range}
              onClick={() => onChange({ ...filters, dateRange: range })}
              className={`rounded-xl border px-3 py-2.5 text-xs font-bold transition ${
                filters.dateRange === range
                  ? 'border-emerald-900 bg-emerald-950 text-white'
                  : 'border-slate-200 bg-white text-slate-600 hover:border-emerald-300'
              }`}
            >
              {labels[range]}
            </button>
          )
        })}
      </div>

      <fieldset>
        <legend className="mb-2 text-xs font-extrabold uppercase tracking-[0.12em] text-slate-500">
          Modalidad
        </legend>
        <div className="flex flex-wrap gap-2">
          {(['all', 'in_person', 'virtual', 'hybrid'] as const).map((modality) => (
            <button
              type="button"
              key={modality}
              onClick={() => onChange({ ...filters, modality })}
              className={`rounded-full px-3 py-2 text-xs font-bold transition ${
                filters.modality === modality
                  ? 'bg-lime-300 text-emerald-950'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {modality === 'all' ? 'Todas' : modalityLabels[modality as EventModality]}
            </button>
          ))}
        </div>
      </fieldset>

      <SelectField id="city" label="Ciudad" value={filters.city} values={cities} onChange={(city) => onChange({ ...filters, city })} />
      <SelectField id="organization" label="Organizador" value={filters.organization} values={organizations} onChange={(organization) => onChange({ ...filters, organization })} />
      <SelectField id="event-type" label="Tipo de evento" value={filters.eventType} values={eventTypes} onChange={(eventType) => onChange({ ...filters, eventType })} />
      <SelectField id="source" label="Fuente" value={filters.source} values={sources} onChange={(source) => onChange({ ...filters, source })} />

      <label className="flex cursor-pointer items-center justify-between rounded-xl border border-slate-200 bg-lime-50 px-4 py-3">
        <span>
          <strong className="block text-sm text-emerald-950">Sólo gratuitos</strong>
          <span className="text-xs text-slate-500">Cuando la fuente lo confirma</span>
        </span>
        <input
          type="checkbox"
          checked={filters.freeOnly}
          onChange={(event) => onChange({ ...filters, freeOnly: event.target.checked })}
          className="size-5 accent-emerald-800"
        />
      </label>
    </div>
  )

  return (
    <>
      <aside className="sticky top-5 hidden self-start rounded-[1.4rem] border border-emerald-950/8 bg-white p-5 shadow-[0_12px_36px_rgba(15,48,38,0.06)] lg:block">
        {content}
      </aside>
      {mobileOpen && (
        <div className="fixed inset-0 z-50 bg-emerald-950/55 p-3 backdrop-blur-sm lg:hidden" role="dialog" aria-modal="true" aria-label="Filtros">
          <div className="ml-auto h-full max-w-sm overflow-y-auto rounded-[1.5rem] bg-white p-5 shadow-2xl">
            <div className="mb-5 flex justify-end">
              <button type="button" onClick={onCloseMobile} className="grid size-10 place-items-center rounded-full bg-slate-100 text-emerald-950" aria-label="Cerrar filtros">
                <X className="size-5" />
              </button>
            </div>
            {content}
            <button type="button" onClick={onCloseMobile} className="mt-6 w-full rounded-xl bg-emerald-950 px-4 py-3 font-bold text-white">
              Ver resultados
            </button>
          </div>
        </div>
      )}
    </>
  )
}

