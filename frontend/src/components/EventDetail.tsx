import {
  ArrowLeft,
  ArrowUpRight,
  Building2,
  CalendarDays,
  Clock3,
  MapPin,
  Radio,
  Share2,
  TicketCheck,
} from 'lucide-react'
import type { ReactNode } from 'react'

import {
  categoryClass,
  categoryLabel,
  formatFullDate,
  modalityLabels,
} from '../lib/events'
import type { TechEvent } from '../types/event'
import { BrandMark } from './BrandMark'

export function EventDetail({
  event,
  onBack,
}: {
  event: TechEvent
  onBack: () => void
}) {
  const registrationUrl = event.registration_url ?? event.source_url

  async function shareEvent() {
    const shareData = { title: event.title, text: `Mira este evento en TechEvents Perú: ${event.title}`, url: window.location.href }
    if (navigator.share) await navigator.share(shareData)
    else await navigator.clipboard.writeText(window.location.href)
  }

  return (
    <div className="min-h-screen bg-[#f3f6f1]">
      <header className="bg-emerald-950">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-5 sm:px-8">
          <BrandMark />
          <button type="button" onClick={onBack} className="flex items-center gap-2 rounded-full border border-white/15 px-4 py-2 text-sm font-bold text-white transition hover:bg-white/10">
            <ArrowLeft className="size-4" /> Volver
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-5 py-8 sm:px-8 sm:py-12">
        <div className="grid gap-8 lg:grid-cols-[1fr_360px]">
          <article className="overflow-hidden rounded-[1.8rem] border border-emerald-950/8 bg-white shadow-[0_16px_50px_rgba(15,48,38,0.08)]">
            <div className="relative min-h-64 overflow-hidden bg-emerald-950 p-7 sm:min-h-80 sm:p-10">
              {event.image_url && <img src={event.image_url} alt="" className="absolute inset-0 size-full object-cover opacity-35" />}
              <div className="absolute inset-0 hero-grid opacity-25" />
              <div className="relative flex h-full min-h-52 flex-col justify-end">
                <div className="mb-5 flex flex-wrap gap-2">
                  <span className={`rounded-full px-3 py-1.5 text-xs font-extrabold ${categoryClass(event.category)}`}>{categoryLabel(event.category)}</span>
                  {event.is_free === true && <span className="rounded-full bg-lime-300 px-3 py-1.5 text-xs font-extrabold text-emerald-950">Gratis</span>}
                  <span className="rounded-full border border-white/20 bg-white/10 px-3 py-1.5 text-xs font-bold text-white">{event.source}</span>
                </div>
                <h1 className="max-w-4xl text-3xl font-black leading-[1.04] tracking-[-0.045em] text-white sm:text-5xl">{event.title}</h1>
                <p className="mt-4 flex items-center gap-2 text-sm font-semibold text-emerald-100/75">
                  <Building2 className="size-4 text-lime-300" /> {event.organization ?? 'Comunidad tecnológica'}
                </p>
              </div>
            </div>

            <div className="p-6 sm:p-9">
              <div className="grid gap-3 sm:grid-cols-2">
                <DetailItem icon={<CalendarDays />} label="Fecha" value={formatFullDate(event.start_date)} />
                <DetailItem icon={<Clock3 />} label="Zona horaria" value={event.timezone} />
                <DetailItem icon={event.modality === 'virtual' ? <Radio /> : <MapPin />} label="Modalidad" value={`${modalityLabels[event.modality]}${event.city ? ` · ${event.city}` : ''}`} />
                <DetailItem icon={<TicketCheck />} label="Acceso" value={event.is_free === true ? 'Entrada gratuita' : event.price ? `${event.currency ?? ''} ${event.price}`.trim() : 'Consultar con el organizador'} />
              </div>

              <section className="mt-10">
                <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-emerald-700">Sobre el evento</p>
                <div className="mt-3 whitespace-pre-line text-base leading-7 text-slate-600">
                  {event.description || 'La fuente no publicó una descripción adicional. Revisa el enlace oficial para conocer todos los detalles.'}
                </div>
              </section>

              {event.tags.length > 0 && (
                <section className="mt-9 border-t border-slate-100 pt-7">
                  <p className="mb-3 text-xs font-extrabold uppercase tracking-[0.16em] text-slate-400">Temas y etiquetas</p>
                  <div className="flex flex-wrap gap-2">
                    {event.tags.map((tag) => <span key={tag} className="rounded-full bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-600">{tag}</span>)}
                  </div>
                </section>
              )}
            </div>
          </article>

          <aside className="self-start lg:sticky lg:top-8">
            <div className="rounded-[1.5rem] bg-lime-300 p-6 text-emerald-950 shadow-[0_16px_40px_rgba(15,48,38,0.12)]">
              <p className="text-xs font-extrabold uppercase tracking-[0.16em]">¿Te interesa?</p>
              <h2 className="mt-2 text-2xl font-black tracking-[-0.035em]">Reserva tu lugar en la página oficial.</h2>
              <p className="mt-3 text-sm leading-6 text-emerald-950/70">La inscripción y cualquier cambio de horario son gestionados por el organizador.</p>
              <a href={registrationUrl} target="_blank" rel="noreferrer" className="mt-6 flex items-center justify-between rounded-xl bg-emerald-950 px-4 py-3.5 text-sm font-extrabold text-white transition hover:bg-emerald-800">
                Ir a la inscripción <ArrowUpRight className="size-4" />
              </a>
              <button type="button" onClick={() => void shareEvent()} className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl border border-emerald-950/20 px-4 py-3 text-sm font-bold transition hover:bg-white/30">
                <Share2 className="size-4" /> Compartir evento
              </button>
            </div>
            <p className="mt-4 px-2 text-xs leading-5 text-slate-400">Información recopilada desde {event.source}. Confirma los detalles en el sitio oficial antes de asistir.</p>
          </aside>
        </div>
      </main>
    </div>
  )
}

function DetailItem({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="flex gap-3 rounded-2xl bg-[#f5f7f3] p-4">
      <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-white text-emerald-700 shadow-sm [&>svg]:size-4">{icon}</span>
      <div>
        <p className="text-[10px] font-extrabold uppercase tracking-[0.14em] text-slate-400">{label}</p>
        <p className="mt-1 text-sm font-bold capitalize text-emerald-950">{value}</p>
      </div>
    </div>
  )
}

