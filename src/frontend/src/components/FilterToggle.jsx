export default function FilterToggle({ filter, onFilterChange, viewFilter, onViewFilterChange }) {
  // Combined filter: status filters + special views
  const filters = [
    { key: 'all', label: 'All', isView: false },
    { key: 'sold', label: 'Sold', isView: false },
    { key: 'active', label: 'Active', isView: false },
    { key: 'favorites', label: 'Favorites', isView: true },
    { key: 'removed', label: 'Removed', isView: true }
  ]

  const handleClick = (f) => {
    if (f.isView) {
      onViewFilterChange(f.key)
    } else {
      onViewFilterChange('main')
      onFilterChange(f.key)
    }
  }

  const isActive = (f) => {
    if (f.isView) {
      return viewFilter === f.key
    }
    return viewFilter === 'main' && filter === f.key
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-sm text-gray-600 font-medium">Filter:</span>
      <div className="flex gap-1">
        {filters.map((f) => (
          <button
            key={f.key}
            onClick={() => handleClick(f)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              isActive(f)
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>
    </div>
  )
}
