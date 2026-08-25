import { CalendarX2, RefreshCw, Settings2 } from 'lucide-react'

export function EventSkeletons() {
  return (
    <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3" aria-label="Cargando eventos">
      {Array.from({ length: 6 }, (_, index) => (
        <div key={index} className="overflow-hidden rounded-[1.4rem] border border-slate-100 bg-white">
          <div className="h-36 animate-pulse bg-emerald-950/90" />
          <div className="grid gap-3 p-5">
            <div className="h-5 w-24 animate-pulse rounded-full bg-slate-100" />
            <div className="h-6 w-5/6 animate-pulse rounded bg-slate-100" />
            <div className="h-4 w-1/2 animate-pulse rounded bg-slate-100" />
            <div className="mt-4 h-20 animate-pulse rounded-xl bg-slate-50" />
          </div>
        </div>
      ))}
    </div>
  )
}

export function EmptyState({ onReset }: { onReset: () => void }) {
  return (
    <div className="rounded-[1.5rem] border border-dashed border-emerald-900/20 bg-white px-6 py-16 text-center">
      <CalendarX2 className="mx-auto size-10 text-emerald-300" />
      <h2 className="mt-4 text-xl font-extrabold text-emerald-950">No encontramos eventos con esos filtros</h2>
      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">Prueba otra categoría, amplía el rango de fechas o limpia la búsqueda.</p>
      <button type="button" onClick={onReset} className="mt-5 rounded-xl bg-emerald-950 px-5 py-3 text-sm font-bold text-white">Limpiar filtros</button>
    </div>
  )
}

export function ConnectionState({ error, onRetry }: { error: string; onRetry: () => void }) {
  const configurationError = error.includes('configurar')
  return (
    <div className="rounded-[1.5rem] border border-amber-200 bg-amber-50 p-6 sm:p-8">
      <div className="flex gap-4">
        <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-amber-100 text-amber-800">{configurationError ? <Settings2 className="size-5" /> : <RefreshCw className="size-5" />}</span>
        <div>
          <h2 className="text-lg font-extrabold text-amber-950">{configurationError ? 'Configura la conexión pública' : 'No pudimos cargar los eventos'}</h2>
          <p className="mt-2 text-sm leading-6 text-amber-900/70">{error}</p>
          {configurationError ? (
            <p className="mt-3 rounded-lg bg-white/70 px-3 py-2 font-mono text-xs text-amber-950">frontend/.env.local → VITE_SUPABASE_URL + VITE_SUPABASE_PUBLISHABLE_KEY</p>
          ) : (
            <button type="button" onClick={onRetry} className="mt-4 rounded-lg bg-amber-900 px-4 py-2 text-sm font-bold text-white">Reintentar</button>
          )}
        </div>
      </div>
    </div>
  )
}

