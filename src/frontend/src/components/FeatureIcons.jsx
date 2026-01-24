import { Home, Maximize2, Bath, Building, BedDouble, ArrowUpDown, Flame, Snowflake, Square, Warehouse, Car } from 'lucide-react'

export default function FeatureIcons({ listing, size = 'default' }) {
  const iconClass = size === 'small' ? 'w-3 h-3' : 'w-4 h-4'
  const textClass = size === 'small' ? 'text-xs' : 'text-sm'
  const gapClass = size === 'small' ? 'gap-2' : 'gap-3'

  // Parse floors_building to get the number
  const getBuildingFloors = () => {
    const floors = listing.floors_building
    if (!floors || floors === -1) return null
    if (typeof floors === 'number') return floors
    const match = String(floors).match(/(\d+)/)
    return match ? match[1] : null
  }

  const buildingFloors = getBuildingFloors()

  // Check for AC
  const hasAC = listing.has_air_conditioning === true ||
    (listing.air_conditioning && listing.air_conditioning !== 'nan' && listing.air_conditioning !== '')

  // Check for heating
  const hasHeating = listing.heating && listing.heating !== 'nan' && listing.heating !== ''

  // Check for balcony or terrace
  const balconies = listing.balconies || 0
  const terraces = listing.terraces || 0
  const hasOutdoor = listing.has_balcony === true || listing.has_terrace === true || balconies > 0 || terraces > 0
  const outdoorTitle = terraces > 0 ? `Terrace${terraces > 1 ? ` (${terraces})` : ''}` :
                       balconies > 0 ? `Balcony${balconies > 1 ? ` (${balconies})` : ''}` :
                       listing.has_terrace ? 'Terrace' : 'Balcony'

  // Check for elevator
  const hasElevator = listing.elevator === true

  // Check for cantina
  const hasCantina = listing.has_cellar === true

  // Check for garage/parking
  const hasGarage = listing.has_garage === true || (listing.parking_spots && listing.parking_spots > 0)

  return (
    <div className="space-y-1">
      {/* Primary features row */}
      <div className={`flex flex-wrap ${gapClass} ${textClass} text-gray-600`}>
        {listing.surface_numeric && (
          <div className="flex items-center" title="Surface area">
            <Maximize2 className={`${iconClass} mr-1`} />
            {listing.surface_numeric} m²
          </div>
        )}
        {listing.rooms_count && (
          <div className="flex items-center" title="Rooms">
            <Home className={`${iconClass} mr-1`} />
            {listing.rooms_count}
          </div>
        )}
        {listing.bedrooms && (
          <div className="flex items-center" title="Bedrooms">
            <BedDouble className={`${iconClass} mr-1`} />
            {listing.bedrooms}
          </div>
        )}
        {listing.bathrooms && (
          <div className="flex items-center" title="Bathrooms">
            <Bath className={`${iconClass} mr-1`} />
            {listing.bathrooms}
          </div>
        )}
        {listing.floor && (
          <div className="flex items-center" title={buildingFloors ? `Floor ${listing.floor} of ${buildingFloors}` : `Floor ${listing.floor}`}>
            <Building className={`${iconClass} mr-1`} />
            {listing.floor}{buildingFloors ? `/${buildingFloors}` : ''}
          </div>
        )}
      </div>

      {/* Secondary features row - icons only for compact display */}
      <div className={`flex flex-wrap ${gapClass} ${textClass} text-gray-500`}>
        {hasElevator && (
          <div className="flex items-center" title="Elevator">
            <ArrowUpDown className={`${iconClass}`} />
          </div>
        )}
        {hasOutdoor && (
          <div className="flex items-center" title={outdoorTitle}>
            <Square className={`${iconClass}`} />
          </div>
        )}
        {hasHeating && (
          <div className="flex items-center" title={`Heating: ${listing.heating}`}>
            <Flame className={`${iconClass}`} />
          </div>
        )}
        {hasAC && (
          <div className="flex items-center" title={`AC: ${listing.air_conditioning || 'Yes'}`}>
            <Snowflake className={`${iconClass}`} />
          </div>
        )}
        {hasCantina && (
          <div className="flex items-center" title="Cantina/Cellar">
            <Warehouse className={`${iconClass}`} />
          </div>
        )}
        {hasGarage && (
          <div className="flex items-center" title={listing.parking_spots > 1 ? `Parking (${listing.parking_spots} spots)` : 'Garage/Parking'}>
            <Car className={`${iconClass}`} />
          </div>
        )}
        {listing.typology && (
          <span className="text-gray-400">{listing.typology}</span>
        )}
      </div>
    </div>
  )
}
