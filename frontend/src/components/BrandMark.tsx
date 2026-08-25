export function BrandMark({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex items-center gap-3" aria-label="TechEvents Perú">
      <div className="relative grid size-10 place-items-center overflow-hidden rounded-xl bg-lime-300 text-emerald-950 shadow-[0_8px_30px_rgba(190,242,100,0.2)]">
        <span className="absolute -right-2 -top-2 size-6 rounded-full border-2 border-emerald-950/20" />
        <svg viewBox="0 0 24 24" className="size-6" aria-hidden="true">
          <path
            d="M7 4v16M17 4v16M4 8h16M4 16h16"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.2"
            strokeLinecap="round"
          />
          <circle cx="17" cy="8" r="2.2" fill="currentColor" />
        </svg>
      </div>
      {!compact && (
        <div>
          <p className="text-[17px] font-extrabold tracking-[-0.03em] text-white">
            TechEvents <span className="text-lime-300">Perú</span>
          </p>
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/55">
            Comunidad en movimiento
          </p>
        </div>
      )}
    </div>
  )
}

