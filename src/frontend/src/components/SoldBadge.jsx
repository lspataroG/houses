export default function SoldBadge({ dateSold }) {
  const formatDate = (dateStr) => {
    if (!dateStr) return null
    try {
      // Convert from YYYY_MM_DD format
      const [year, month, day] = dateStr.split('_')
      const date = new Date(year, month - 1, day)
      return date.toLocaleDateString('it-IT', { day: 'numeric', month: 'short' })
    } catch {
      return null
    }
  }

  const formattedDate = formatDate(dateSold)

  return (
    <div className="absolute bottom-2 right-2 pointer-events-none z-10">
      <span className="bg-red-600 text-white px-3 py-1.5 rounded-lg text-sm font-bold shadow-lg">
        SOLD{formattedDate && ` ${formattedDate}`}
      </span>
    </div>
  )
}
