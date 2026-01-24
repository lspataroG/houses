import { useEffect, useMemo } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import { Link } from 'react-router-dom'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { MapPin, ExternalLink } from 'lucide-react'
import { getImageUrls } from '../api/listings'
import FeatureIcons from './FeatureIcons'

// Create custom marker icons
const createIcon = (isActive) => {
  const size = isActive ? 35 : 25
  const color = isActive ? '#2563eb' : '#6b7280' // blue-600 : gray-500

  return L.divIcon({
    className: 'custom-marker',
    html: `
      <div style="
        width: ${size}px;
        height: ${size}px;
        background-color: ${color};
        border: 3px solid white;
        border-radius: 50%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        transform: translate(-50%, -50%);
        transition: all 0.2s ease;
        ${isActive ? 'z-index: 1000;' : ''}
      "></div>
    `,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  })
}

// Component to fly to active marker
function FlyToActive({ listings, activeListingId }) {
  const map = useMap()

  useEffect(() => {
    if (activeListingId) {
      const listing = listings.find(l => l.id === activeListingId)
      if (listing && listing.latitude && listing.longitude) {
        map.flyTo([listing.latitude, listing.longitude], map.getZoom(), {
          duration: 0.5
        })
      }
    }
  }, [activeListingId, listings, map])

  return null
}

export default function MapView({ listings, activeListingId, onMarkerClick }) {
  // Filter listings with valid coordinates
  const validListings = useMemo(() =>
    listings.filter(l => l.latitude && l.longitude),
    [listings]
  )

  // Calculate center of map
  const center = useMemo(() => {
    if (validListings.length === 0) return [44.49, 11.34] // Default to Bologna
    return [
      validListings.reduce((sum, l) => sum + l.latitude, 0) / validListings.length,
      validListings.reduce((sum, l) => sum + l.longitude, 0) / validListings.length,
    ]
  }, [validListings])

  const formatPrice = (price) => {
    if (!price) return 'N/A'
    return new Intl.NumberFormat('it-IT', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0,
    }).format(price)
  }

  if (validListings.length === 0) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <MapPin className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No listings with location data</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full w-full">
      <MapContainer
        center={center}
        zoom={15}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <FlyToActive listings={validListings} activeListingId={activeListingId} />

        {validListings.map((listing) => {
          const isActive = listing.id === activeListingId
          const images = getImageUrls(listing)
          const firstImage = images[0]

          return (
            <Marker
              key={listing.id}
              position={[listing.latitude, listing.longitude]}
              icon={createIcon(isActive)}
              zIndexOffset={isActive ? 1000 : 0}
              eventHandlers={{
                click: () => onMarkerClick && onMarkerClick(listing.id)
              }}
            >
              <Popup>
                <div className="min-w-[250px]">
                  {firstImage && (
                    <img
                      src={firstImage}
                      alt={listing.title}
                      className="w-full h-32 object-cover rounded mb-2"
                    />
                  )}

                  <Link
                    to={`/listing/${listing.id}`}
                    className="font-bold text-sm mb-1 hover:text-blue-600 block line-clamp-2"
                  >
                    {listing.title}
                  </Link>

                  <div className="text-lg font-bold text-blue-600 mb-2">
                    {formatPrice(listing.price)}
                  </div>

                  <div className="mb-2">
                    <FeatureIcons listing={listing} size="small" />
                  </div>

                  <div className="mb-2">
                    <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs font-medium">
                      {listing.portal}
                    </span>
                    {listing.is_sold && (
                      <span className="bg-red-100 text-red-700 px-2 py-1 rounded text-xs font-medium ml-1">
                        SOLD
                      </span>
                    )}
                  </div>

                  {!listing.is_sold && (
                    <a
                      href={listing.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-xs text-blue-600 hover:underline"
                    >
                      View on {listing.portal} <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              </Popup>
            </Marker>
          )
        })}
      </MapContainer>
    </div>
  )
}
