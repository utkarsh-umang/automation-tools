import { Filter } from 'lucide-react'
import { useState } from 'react'
import { ThumbnailDetailModal } from './ThumbnailDetailModal'

const thumbnails = [
  {
    id: 1,
    status: 'LIVE',
    title: 'The Future of AI Architecture',
    description: 'Exploration of how machine learning is reshaping the technical landscape.',
    views: '2.4K',
    updatedAt: '2 hours ago',
    image: 'https://images.unsplash.com/photo-1620641788421-7a1c342ea42e?q=80&w=600&auto=format&fit=crop'
  },
  {
    id: 2,
    status: 'DRAFT',
    title: '10 Tips for Minimalist Code',
    description: 'A deep dive into clean architecture and best practices.',
    views: '--',
    createdAt: 'Jan 12, 2024',
    image: 'https://images.unsplash.com/photo-1544256718-3bcf237f3974?q=80&w=600&auto=format&fit=crop'
  },
  {
    id: 3,
    status: 'LIVE',
    title: 'Vintage Tech in 2024?',
    description: 'Why the analog revival is gaining momentum in a digital world.',
    views: '15.8K',
    updatedAt: '1 day ago',
    image: 'https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=600&auto=format&fit=crop'
  },
  {
    id: 4,
    status: 'LIVE',
    title: 'Global Connectivity: Part II',
    description: 'Understanding the infrastructure that powers our modern networks.',
    views: '42.1K',
    updatedAt: '3 days ago',
    image: 'https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=600&auto=format&fit=crop'
  }
]

export function YourThumbnails() {
  const [selectedThumbnail, setSelectedThumbnail] = useState<any>(null)

  return (
    <>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold" style={{ color: '#111827' }}>
          Recent thumbnails
        </h2>
        <button
          type="button"
          className="flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-semibold transition-colors"
          style={{ borderColor: '#e5e7eb', color: '#374151', backgroundColor: '#ffffff' }}
          onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#f9fafb' }}
          onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '#ffffff' }}
        >
          <Filter className="w-3.5 h-3.5" /> Filter
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-2">
         {thumbnails.map(item => (
            <button 
              key={item.id} 
              type="button"
              className="w-full text-left rounded-xl overflow-hidden transition-shadow flex h-36"
              style={{
                border: '1px solid #e5e7eb',
                backgroundColor: '#ffffff',
                boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(37,99,235,0.1)'
                e.currentTarget.style.borderColor = 'rgba(37,99,235,0.25)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.05)'
                e.currentTarget.style.borderColor = '#e5e7eb'
              }}
              onClick={() => setSelectedThumbnail(item)}
            >
               <div className="w-40 flex-shrink-0 bg-black relative flex items-center justify-center p-1 border-r" style={{ borderColor: '#e5e7eb' }}>
                  <img src={item.image} alt={item.title} className="w-full h-full object-cover rounded shadow-sm opacity-90 transition-opacity hover:opacity-100" />
               </div>
               <div className="p-4 flex flex-col justify-between flex-1 min-w-0">
                  <div>
                    <div className="flex justify-between items-start mb-1">
                      <h3 className="truncate text-base font-semibold" style={{ color: '#0a0f1e' }}>{item.title}</h3>
                      <span
                        className="rounded px-2 py-0.5 text-[10px] font-semibold"
                        style={item.status === 'LIVE' ? {
                          backgroundColor: '#f0fdf4',
                          border: '1px solid #bbf7d0',
                          color: '#15803d',
                        } : {
                          backgroundColor: '#f9fafb',
                          border: '1px solid #e5e7eb',
                          color: '#6b7280',
                        }}
                      >
                        {item.status}
                      </span>
                    </div>
                    <p className="line-clamp-2 text-sm leading-relaxed" style={{ color: '#6b7280' }}>
                      {item.description}
                    </p>
                  </div>
                  <div className="mt-2 text-xs" style={{ color: '#9ca3af' }}>
                     {item.views !== '--' && <span style={{ color: '#374151', fontWeight: 500 }}>{item.views} views • </span>} 
                     {item.updatedAt ? `Updated ${item.updatedAt}` : `Created ${item.createdAt}`}
                  </div>
               </div>
            </button>
         ))}
      </div>

      {selectedThumbnail && (
        <ThumbnailDetailModal 
          thumbnail={selectedThumbnail} 
          onClose={() => setSelectedThumbnail(null)} 
        />
      )}
    </>
  )
}
