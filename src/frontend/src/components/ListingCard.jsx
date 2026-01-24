import { useState } from 'react'
import { Link } from 'react-router-dom'
import { MapPin, ExternalLink, Clock, LayoutGrid, Heart, Trash2, RotateCcw, Calendar, RefreshCw } from 'lucide-react'
import ImageGallery from './ImageGallery'
import Lightbox from './Lightbox'
import SoldBadge from './SoldBadge'
import FeatureIcons from './FeatureIcons'
import { getImageUrls, getFloorPlanUrls } from '../api/listings'

export default function ListingCard({ listing, isFavorite, isRemoved, onToggleFavorite, onToggleRemoved, onRestore, viewFilter }) {
  const [lightboxOpen, setLightboxOpen] = useState(false)
  const [lightboxIndex, setLightboxIndex] = useState(0)
  const [showFloorPlans, setShowFloorPlans] = useState(false)

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

  const formatPrice = (price) => {
    if (!price) return 'N/A'
    return new Intl.NumberFormat('it-IT', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0,
    }).format(price)
  }

  const formatDate = (dateValue) => {
    if (!dateValue) return null
    try {
      // Handle Unix timestamp (seconds)
      const date = typeof dateValue === 'number' && dateValue > 1e9
        ? new Date(dateValue * 1000)
        : new Date(dateValue)
      if (isNaN(date.getTime())) return null
      return date.toLocaleDateString('it-IT', { day: 'numeric', month: 'short', year: 'numeric' })
    } catch {
      return null
    }
  }

  const getDaysAgo = (dateValue) => {
    if (!dateValue) return null
    try {
      const date = typeof dateValue === 'number' && dateValue > 1e9
        ? new Date(dateValue * 1000)
        : new Date(dateValue)
      if (isNaN(date.getTime())) return null
      const now = new Date()
      const diffMs = now - date
      const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
      return diffDays
    } catch {
      return null
    }
  }

  const createdDate = formatDate(listing.created_at)
  const createdDaysAgo = getDaysAgo(listing.created_at)
  const updatedDaysAgo = getDaysAgo(listing.updated_at || listing.last_update)
  const isNew = createdDaysAgo !== null && createdDaysAgo <= 7

  return (
    <>
      <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-xl transition-shadow">
        {/* Image Gallery */}
        <div className="relative aspect-video bg-gray-200">
          <ImageGallery
            images={images}
            onImageClick={handleImageClick}
          />

          {/* Sold overlay */}
          {listing.is_sold && <SoldBadge />}

          {/* Portal badge */}
          <div className="absolute top-2 left-2 flex gap-1">
            <span className="bg-blue-600 text-white px-2 py-1 rounded text-xs font-medium">
              {listing.portal}
            </span>
            {isNew && (
              <span className="bg-green-500 text-white px-2 py-1 rounded text-xs font-medium">
                NEW
              </span>
            )}
            {listing.is_sold && listing.days_live && (
              <span className="bg-orange-500 text-white px-2 py-1 rounded text-xs font-medium flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {Math.round(listing.days_live)}d
              </span>
            )}
          </div>

          {/* Action buttons (top right) */}
          <div className="absolute top-2 right-2 flex gap-1">
            {/* Heart button - always visible */}
            <button
              onClick={(e) => { e.stopPropagation(); onToggleFavorite?.(listing.id); }}
              className={`p-2 rounded-full shadow-md transition-colors ${
                isFavorite
                  ? 'bg-red-500 hover:bg-red-600'
                  : 'bg-white/90 hover:bg-white'
              }`}
              title={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
            >
              <Heart
                className={`w-4 h-4 ${isFavorite ? 'text-white fill-white' : 'text-gray-600'}`}
              />
            </button>

            {/* Trash button - only in main/favorites view */}
            {viewFilter !== 'removed' && (
              <button
                onClick={(e) => { e.stopPropagation(); onToggleRemoved?.(listing.id); }}
                className="p-2 rounded-full bg-white/90 hover:bg-white shadow-md transition-colors"
                title="Remove listing"
              >
                <Trash2 className="w-4 h-4 text-gray-600" />
              </button>
            )}

            {/* Restore button - only in removed view */}
            {viewFilter === 'removed' && (
              <button
                onClick={(e) => { e.stopPropagation(); onRestore?.(listing.id); }}
                className="p-2 rounded-full bg-white/90 hover:bg-white shadow-md transition-colors"
                title="Restore listing"
              >
                <RotateCcw className="w-4 h-4 text-green-600" />
              </button>
            )}
          </div>
        </div>

        {/* Content */}
        <div className="p-4">
          {/* Title - links to original URL if active, or detail page if sold */}
          {listing.is_sold ? (
            <Link
              to={`/listing/${listing.id}`}
              className="font-bold text-lg mb-2 line-clamp-2 hover:text-blue-600 block"
            >
              {listing.title}
            </Link>
          ) : (
            <a
              href={listing.url}
              target="_blank"
              rel="noopener noreferrer"
              className="font-bold text-lg mb-2 line-clamp-2 hover:text-blue-600 block"
            >
              {listing.title}
            </a>
          )}

          {/* Location */}
          {listing.location && (
            <div className="flex items-center text-gray-600 text-sm mb-2">
              <MapPin className="w-4 h-4 mr-1 flex-shrink-0" />
              <span className="truncate">{listing.location}</span>
            </div>
          )}

          {/* Date info */}
          {createdDate && (
            <div className="flex items-center gap-1 text-gray-500 text-xs mb-2">
              <Calendar className="w-3 h-3" />
              {createdDate}
              {createdDaysAgo !== null && (
                <span className="text-gray-400">
                  ({createdDaysAgo === 0 ? 'Today' : createdDaysAgo === 1 ? 'Yesterday' : `${createdDaysAgo} days ago`})
                </span>
              )}
            </div>
          )}

          {/* Price */}
          <div className="text-2xl font-bold text-blue-600 mb-3">
            {formatPrice(listing.price)}
          </div>

          {/* Features */}
          <div className="mb-4">
            <FeatureIcons listing={listing} />
          </div>

          {/* Actions */}
          <div className="flex items-center gap-3">
            {listing.is_sold && (
              <Link
                to={`/listing/${listing.id}`}
                className="inline-flex items-center gap-1 text-sm text-blue-600 hover:underline"
              >
                View details
                <ExternalLink className="w-3 h-3" />
              </Link>
            )}
            {floorPlans.length > 0 && (
              <button
                onClick={handleFloorPlanClick}
                className="inline-flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900 bg-gray-100 hover:bg-gray-200 px-2 py-1 rounded transition-colors"
              >
                <LayoutGrid className="w-3 h-3" />
                Floor Plan
              </button>
            )}
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
    </>
  )
}
