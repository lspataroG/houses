import { useEffect, useCallback } from 'react'
import { X, ChevronLeft, ChevronRight } from 'lucide-react'

export default function Lightbox({ images, currentIndex, onClose, onIndexChange }) {
  const goToPrevious = useCallback(() => {
    onIndexChange((currentIndex - 1 + images.length) % images.length)
  }, [currentIndex, images.length, onIndexChange])

  const goToNext = useCallback(() => {
    onIndexChange((currentIndex + 1) % images.length)
  }, [currentIndex, images.length, onIndexChange])

  useEffect(() => {
    const handleKeyDown = (e) => {
      switch (e.key) {
        case 'Escape':
          onClose()
          break
        case 'ArrowLeft':
          goToPrevious()
          break
        case 'ArrowRight':
          goToNext()
          break
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    document.body.style.overflow = 'hidden'

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = ''
    }
  }, [onClose, goToPrevious, goToNext])

  return (
    <div
      className="fixed inset-0 bg-black/90 flex items-center justify-center"
      style={{ zIndex: 9999 }}
      onClick={onClose}
    >
      {/* Close button */}
      <button
        onClick={onClose}
        className="absolute top-4 right-4 text-white/80 hover:text-white p-2 z-10"
      >
        <X className="w-8 h-8" />
      </button>

      {/* Image counter */}
      <div className="absolute top-4 left-4 text-white/80 text-lg">
        {currentIndex + 1} / {images.length}
      </div>

      {/* Navigation */}
      {images.length > 1 && (
        <>
          <button
            onClick={(e) => {
              e.stopPropagation()
              goToPrevious()
            }}
            className="absolute left-4 top-1/2 -translate-y-1/2 text-white/80 hover:text-white p-2"
          >
            <ChevronLeft className="w-12 h-12" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation()
              goToNext()
            }}
            className="absolute right-4 top-1/2 -translate-y-1/2 text-white/80 hover:text-white p-2"
          >
            <ChevronRight className="w-12 h-12" />
          </button>
        </>
      )}

      {/* Main image */}
      <img
        src={images[currentIndex]}
        alt={`Image ${currentIndex + 1}`}
        className="max-h-[90vh] max-w-[90vw] object-contain"
        onClick={(e) => e.stopPropagation()}
      />
    </div>
  )
}
