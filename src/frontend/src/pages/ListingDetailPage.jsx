import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, MapPin, ExternalLink, Calendar, Building, Thermometer, Zap, Car, Check, Clock, LayoutGrid } from 'lucide-react'
import Header from '../components/Header'
import ImageGallery from '../components/ImageGallery'
import Lightbox from '../components/Lightbox'
import SoldBadge from '../components/SoldBadge'
import FeatureIcons from '../components/FeatureIcons'
import { fetchListing, getImageUrls, getFloorPlanUrls } from '../api/listings'

export default function ListingDetailPage() {
  const { id } = useParams()
  const [listing, setListing] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lightboxOpen, setLightboxOpen] = useState(false)
  const [lightboxIndex, setLightboxIndex] = useState(0)
  const [showFloorPlans, setShowFloorPlans] = useState(false)

  useEffect(() => {
    loadListing()
  }, [id])

  const loadListing = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchListing(id)
      setListing(data)
    } catch (err) {
      setError(err.message)
    }
    setLoading(false)
  }

  const formatPrice = (price) => {
    if (!price) return 'N/A'
    return new Intl.NumberFormat('it-IT', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0,
    }).format(price)
  }

  const formatDate = (timestamp) => {
    if (!timestamp) return null
    const date = new Date(typeof timestamp === 'number' ? timestamp * 1000 : timestamp)
    return date.toLocaleDateString('it-IT', { year: 'numeric', month: 'long', day: 'numeric' })
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading listing...</p>
        </div>
      </div>
    )
  }

  if (error || !listing) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="max-w-4xl mx-auto px-4 py-12">
          <div className="text-center bg-white rounded-lg p-8">
            <p className="text-red-500 text-lg mb-4">{error || 'Listing not found'}</p>
            <Link to="/" className="text-blue-600 hover:underline">
              Back to listings
            </Link>
          </div>
        </div>
      </div>
    )
  }

  const images = getImageUrls(listing)
  const floorPlans = getFloorPlanUrls(listing)

  const handleImageClick = (index) => {
    setShowFloorPlans(false)
    setLightboxIndex(index)
    setLightboxOpen(true)
  }

  const handleFloorPlanClick = () => {
    setShowFloorPlans(true)
    setLightboxIndex(0)
    setLightboxOpen(true)
  }

  // Collect all characteristics/features
  const characteristics = listing.characteristics || []

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <div className="max-w-6xl mx-auto px-4 py-6">
        {/* Back button */}
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to listings
        </Link>

        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          {/* Image Gallery */}
          <div className="relative aspect-video md:aspect-[21/9] bg-gray-200">
            <ImageGallery
              images={images}
              onImageClick={handleImageClick}
            />
            {listing.is_sold && <SoldBadge />}
            {floorPlans.length > 0 && (
              <button
                onClick={handleFloorPlanClick}
                className="absolute bottom-4 left-4 bg-white/90 hover:bg-white text-gray-800 px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-2 shadow-lg transition-colors"
              >
                <LayoutGrid className="w-4 h-4" />
                Floor Plan ({floorPlans.length})
              </button>
            )}
          </div>

          {/* Content */}
          <div className="p-6">
            {/* Header */}
            <div className="flex flex-wrap items-start justify-between gap-4 mb-6">
              <div>
                <h1 className="text-2xl md:text-3xl font-bold mb-2">{listing.title}</h1>
                {listing.location && (
                  <div className="flex items-center text-gray-600">
                    <MapPin className="w-5 h-5 mr-2" />
                    {listing.location}
                  </div>
                )}
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-blue-600">
                  {formatPrice(listing.price)}
                </div>
                {listing.price_per_sqm && (
                  <div className="text-sm text-gray-500">
                    {formatPrice(listing.price_per_sqm)}/m2
                  </div>
                )}
              </div>
            </div>

            {/* Portal, sold info, and external link */}
            <div className="flex items-center gap-4 mb-6 flex-wrap">
              <span className="bg-blue-600 text-white px-3 py-1 rounded text-sm font-medium">
                {listing.portal}
              </span>
              {listing.is_sold && (
                <span className="bg-red-600 text-white px-3 py-1 rounded text-sm font-medium">
                  SOLD
                </span>
              )}
              {listing.is_sold && listing.days_live && (
                <span className="bg-orange-500 text-white px-3 py-1 rounded text-sm font-medium flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  Sold in {Math.round(listing.days_live)} days
                </span>
              )}
              {!listing.is_sold && (
                <a
                  href={listing.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-blue-600 hover:underline"
                >
                  View original listing
                  <ExternalLink className="w-4 h-4" />
                </a>
              )}
            </div>

            {/* Key Features */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-gray-50 rounded-lg mb-6">
              <FeatureIcons listing={listing} />
            </div>

            {/* Details Grid */}
            <div className="grid md:grid-cols-2 gap-6 mb-6">
              {/* Property Details */}
              <div>
                <h2 className="text-lg font-semibold mb-4">Property Details</h2>
                <dl className="space-y-2">
                  {listing.condition && (
                    <div className="flex justify-between py-2 border-b">
                      <dt className="text-gray-600">Condition</dt>
                      <dd className="font-medium">{listing.condition}</dd>
                    </div>
                  )}
                  {listing.building_year && (
                    <div className="flex justify-between py-2 border-b">
                      <dt className="text-gray-600">Year Built</dt>
                      <dd className="font-medium">{listing.building_year}</dd>
                    </div>
                  )}
                  {listing.heating && (
                    <div className="flex justify-between py-2 border-b">
                      <dt className="text-gray-600">Heating</dt>
                      <dd className="font-medium">{listing.heating}</dd>
                    </div>
                  )}
                  {listing.energy_class && (
                    <div className="flex justify-between py-2 border-b">
                      <dt className="text-gray-600">Energy Class</dt>
                      <dd className="font-medium">{listing.energy_class}</dd>
                    </div>
                  )}
                  {listing.condominium_fees && (
                    <div className="flex justify-between py-2 border-b">
                      <dt className="text-gray-600">Condo Fees</dt>
                      <dd className="font-medium">{listing.condominium_fees}</dd>
                    </div>
                  )}
                </dl>
              </div>

              {/* Amenities */}
              <div>
                <h2 className="text-lg font-semibold mb-4">Amenities</h2>
                <div className="grid grid-cols-2 gap-2">
                  {listing.has_balcony && (
                    <div className="flex items-center gap-2 text-green-600">
                      <Check className="w-4 h-4" />
                      <span>Balcony</span>
                    </div>
                  )}
                  {listing.has_terrace && (
                    <div className="flex items-center gap-2 text-green-600">
                      <Check className="w-4 h-4" />
                      <span>Terrace</span>
                    </div>
                  )}
                  {listing.has_garden && (
                    <div className="flex items-center gap-2 text-green-600">
                      <Check className="w-4 h-4" />
                      <span>Garden</span>
                    </div>
                  )}
                  {listing.has_cellar && (
                    <div className="flex items-center gap-2 text-green-600">
                      <Check className="w-4 h-4" />
                      <span>Cellar</span>
                    </div>
                  )}
                  {listing.has_air_conditioning && (
                    <div className="flex items-center gap-2 text-green-600">
                      <Check className="w-4 h-4" />
                      <span>Air Conditioning</span>
                    </div>
                  )}
                  {listing.elevator && (
                    <div className="flex items-center gap-2 text-green-600">
                      <Check className="w-4 h-4" />
                      <span>Elevator</span>
                    </div>
                  )}
                  {listing.parking && (
                    <div className="flex items-center gap-2 text-green-600">
                      <Car className="w-4 h-4" />
                      <span>{listing.parking}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Characteristics */}
            {characteristics.length > 0 && (
              <div className="mb-6">
                <h2 className="text-lg font-semibold mb-4">Characteristics</h2>
                <div className="flex flex-wrap gap-2">
                  {characteristics.map((char, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
                    >
                      {char}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Description */}
            {listing.description && (
              <div className="mb-6">
                <h2 className="text-lg font-semibold mb-4">Description</h2>
                <div className="prose prose-gray max-w-none">
                  <p className="text-gray-700 whitespace-pre-line">{listing.description}</p>
                </div>
              </div>
            )}

            {/* Metadata */}
            <div className="text-sm text-gray-500 pt-4 border-t">
              {listing.created_at && (
                <p>Listed: {formatDate(listing.created_at)}</p>
              )}
              {listing.last_update && (
                <p>{listing.last_update}</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Lightbox */}
      {lightboxOpen && (
        <Lightbox
          images={showFloorPlans ? floorPlans : images}
          currentIndex={lightboxIndex}
          onClose={() => setLightboxOpen(false)}
          onIndexChange={setLightboxIndex}
        />
      )}
    </div>
  )
}
