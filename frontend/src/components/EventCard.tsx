import {
  ArrowUpRight,
  Building2,
  CalendarDays,
  MapPin,
  Radio,
} from 'lucide-react'

import {
  categoryClass,
  categoryLabel,
  formatEventDate,
  formatEventTime,
  modalityLabels,
} from '../lib/events'
import type { TechEvent } from '../types/event'

interface EventCardProps {
  event: TechEvent
  onSelect: (event: TechEvent) => void
}

export function EventCard({ event, onSelect }: EventCardProps) {
  const day = new Intl.DateTimeFormat('es-PE', { day: '2-digit' }).format(
    new Date(event.start_date),
  )
  const month = new Intl.DateTimeFormat('es-PE', { month: 'short' })
    .format(new Date(event.start_date))
    .replace('.', '')

  return (
    <article className="group flex h-full flex-col overflow-hidden rounded-[1.4rem] border border-emerald-950/8 bg-white shadow-[0_12px_36px_rgba(15,48,38,0.07)] transition duration-300 hover:-translate-y-1 hover:border-emerald-700/20 hover:shadow-[0_18px_45px_rgba(15,48,38,0.12)]">
      <div className="relative h-36 overflow-hidden bg-emerald-950">
        {event.image_url ? (
          <img
            src={event.image_url}
            alt=""
            className="size-full object-cover opacity-80 transition duration-500 group-hover:scale-105"
            loading="lazy"
          />
        ) : (
          <div className="absolute inset-0 event-card-pattern" aria-hidden="true">
            <div className="absolute -right-8 -top-16 size-40 rounded-full border border-lime-300/25" />
            <div className="absolute right-4 top-4 size-16 rounded-full bg-lime-300/10 blur-xl" />
            <span className="absolute bottom-5 left-6 text-6xl font-black tracking-[-0.08em] text-white/8">
              {event.source}
            </span>
          </div>
        )}
        <div className="absolute left-4 top-4 rounded-xl bg-white px-3 py-2 text-center shadow-lg">
          <strong className="block text-xl leading-none text-emerald-950">{day}</strong>
          <span className="mt-1 block text-[10px] font-extrabold uppercase tracking-[0.16em] text-emerald-700">
            {month}
          </span>
        </div>
        <span className="absolute right-4 top-4 rounded-full border border-white/20 bg-emerald-950/75 px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.12em] text-white backdrop-blur">
          {event.source}
        </span>
      </div>

      <div className="flex flex-1 flex-col p-5">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <span className={`rounded-full px-2.5 py-1 text-[11px] font-bold ${categoryClass(event.category)}`}>
            {categoryLabel(event.category)}
          </span>
          {event.is_free === true && (
            <span className="rounded-full bg-lime-200 px-2.5 py-1 text-[11px] font-extrabold text-emerald-950">
              Gratis
            </span>
          )}
        </div>

        <h2 className="line-clamp-2 text-xl font-extrabold leading-tight tracking-[-0.025em] text-emerald-950">
          {event.title}
        </h2>
        <p className="mt-2 flex items-center gap-2 text-sm font-semibold text-slate-500">
          <Building2 className="size-4 text-emerald-600" aria-hidden="true" />
          <span className="truncate">{event.organization ?? 'Comunidad tecnológica'}</span>
        </p>

        <div className="my-5 grid gap-2.5 border-y border-slate-100 py-4 text-sm text-slate-600">
          <p className="flex items-center gap-2.5">
            <CalendarDays className="size-4 text-emerald-700" aria-hidden="true" />
            <span className="capitalize">{formatEventDate(event.start_date)}</span>
            <span className="text-slate-300">•</span>
            <span>{formatEventTime(event.start_date)}</span>
          </p>
          <p className="flex items-center gap-2.5">
            {event.modality === 'virtual' ? (
              <Radio className="size-4 text-emerald-700" aria-hidden="true" />
            ) : (
              <MapPin className="size-4 text-emerald-700" aria-hidden="true" />
            )}
            <span>{modalityLabels[event.modality]}</span>
            {event.city && <span className="text-slate-400">· {event.city}</span>}
          </p>
        </div>

        <button
          type="button"
          onClick={() => onSelect(event)}
          className="mt-auto flex w-full items-center justify-between rounded-xl bg-emerald-950 px-4 py-3 text-sm font-bold text-white transition hover:bg-emerald-800 focus:outline-none focus:ring-2 focus:ring-emerald-700 focus:ring-offset-2"
        >
          Ver evento
          <ArrowUpRight className="size-4 transition group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
        </button>
      </div>
    </article>
  )
}

