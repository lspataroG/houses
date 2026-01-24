import { Home, Maximize2, Bath, Building } from 'lucide-react'

export default function FeatureIcons({ listing, size = 'default' }) {
  const iconClass = size === 'small' ? 'w-3 h-3' : 'w-4 h-4'
  const textClass = size === 'small' ? 'text-xs' : 'text-sm'
  const gapClass = size === 'small' ? 'gap-3' : 'gap-4'

  return (
    <div className={`flex ${gapClass} ${textClass} text-gray-600`}>
      {listing.rooms_count && (
        <div className="flex items-center">
          <Home className={`${iconClass} mr-1`} />
          {listing.rooms_count} rooms
        </div>
      )}
      {listing.surface_numeric && (
        <div className="flex items-center">
          <Maximize2 className={`${iconClass} mr-1`} />
          {listing.surface_numeric} m2
        </div>
      )}
      {listing.bathrooms && (
        <div className="flex items-center">
          <Bath className={`${iconClass} mr-1`} />
          {listing.bathrooms}
        </div>
      )}
      {listing.floor && (
        <div className="flex items-center">
          <Building className={`${iconClass} mr-1`} />
          {listing.floor}
        </div>
      )}
    </div>
  )
}
