import { useState } from 'react'
import { ChevronLeft, ChevronRight, Home } from 'lucide-react'

export default function ImageGallery({ images, onImageClick, showCounter = true }) {
  const [currentIndex, setCurrentIndex] = useState(0)

  const prevImage = (e) => {
    e.stopPropagation()
    setCurrentIndex((prev) => (prev - 1 + images.length) % images.length)
  }

  const nextImage = (e) => {
    e.stopPropagation()
    setCurrentIndex((prev) => (prev + 1) % images.length)
  }

  const handleImageClick = () => {
    if (onImageClick) {
      onImageClick(currentIndex)
    }
  }

  if (images.length === 0) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-200 text-gray-400">
        <Home className="w-16 h-16" />
      </div>
    )
  }

  return (
    <div className="relative w-full h-full">
      <img
        src={images[currentIndex]}
        alt={`Image ${currentIndex + 1}`}
        className="w-full h-full object-cover cursor-pointer"
        onClick={handleImageClick}
      />

      {images.length > 1 && (
        <>
          <button
            onClick={prevImage}
            className="absolute left-2 top-1/2 -translate-y-1/2 bg-black/50 text-white p-2 rounded-full hover:bg-black/70 transition-colors"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <button
            onClick={nextImage}
            className="absolute right-2 top-1/2 -translate-y-1/2 bg-black/50 text-white p-2 rounded-full hover:bg-black/70 transition-colors"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
          {showCounter && (
            <div className="absolute bottom-2 right-2 bg-black/50 text-white px-2 py-1 rounded text-sm">
              {currentIndex + 1} / {images.length}
            </div>
          )}
        </>
      )}
    </div>
  )
}
