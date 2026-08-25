import { ArrowUpRight, MapPin, Radio } from 'lucide-react'

import { formatEventTime, groupEventsByDay, modalityLabels } from '../lib/events'
import type { TechEvent } from '../types/event'

export function AgendaView({ events, onSelect }: { events: TechEvent[]; onSelect: (event: TechEvent) => void }) {
  return (
    <div className="grid gap-5">
      {groupEventsByDay(events).map(([day, dayEvents]) => (
        <section key={day} className="overflow-hidden rounded-[1.4rem] border border-emerald-950/8 bg-white shadow-[0_10px_30px_rgba(15,48,38,0.05)]">
          <header className="border-b border-slate-100 bg-[#f7f9f5] px-5 py-4 sm:px-6">
            <h2 className="font-extrabold capitalize tracking-[-0.02em] text-emerald-950">
              {new Intl.DateTimeFormat('es-PE', { weekday: 'long', day: 'numeric', month: 'long' }).format(new Date(`${day}T12:00:00`))}
            </h2>
          </header>
          <div className="divide-y divide-slate-100">
            {dayEvents.map((event) => (
              <button type="button" key={event.id} onClick={() => onSelect(event)} className="group grid w-full gap-3 px-5 py-5 text-left transition hover:bg-lime-50/60 sm:grid-cols-[90px_1fr_auto] sm:items-center sm:px-6">
                <p className="text-sm font-extrabold text-emerald-800">{formatEventTime(event.start_date)}</p>
                <div>
                  <h3 className="font-extrabold leading-snug text-emerald-950 group-hover:text-emerald-700">{event.title}</h3>
                  <div className="mt-1.5 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                    <span>{event.organization ?? event.source}</span><span>·</span>
                    <span className="flex items-center gap-1">{event.modality === 'virtual' ? <Radio className="size-3" /> : <MapPin className="size-3" />}{modalityLabels[event.modality]}{event.city ? ` · ${event.city}` : ''}</span>
                  </div>
                </div>
                <ArrowUpRight className="hidden size-4 text-emerald-700 transition group-hover:-translate-y-0.5 group-hover:translate-x-0.5 sm:block" />
              </button>
            ))}
          </div>
        </section>
      ))}
    </div>
  )
}

