import { UploadCloud, Image as ImageIcon, ChevronDown } from 'lucide-react'
import { useState } from 'react'

export function CreateThumbnail() {
  const [includeText, setIncludeText] = useState(true)

  return (
    <div
      className="w-full rounded-xl"
      style={{
        border: '1px solid #e5e7eb',
        backgroundColor: '#ffffff',
        boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
      }}
    >
      <div
        className="px-5 py-4 rounded-t-xl"
        style={{
          background: 'linear-gradient(90deg, #0a0f1e 0%, #0f1f4a 100%)',
          borderBottom: '1px solid rgba(37,99,235,0.2)',
        }}
      >
        <h2 className="text-base font-semibold" style={{ color: '#ffffff' }}>
          Create new thumbnail
        </h2>
        <p className="mt-1 text-xs" style={{ color: 'rgba(255,255,255,0.55)' }}>
          Define your visual strategy and generate high-impact editorial assets.
        </p>
      </div>

      <div className="space-y-6 px-5 py-5">
         <div>
            <label className="mb-1.5 block text-sm font-medium" style={{ color: '#111827' }}>
               Thumbnail title <span style={{ color: '#be123c' }}>*</span>
            </label>
            <input 
              type="text" 
              placeholder="e.g. 10 Life Hacks for Designers" 
              className="w-full rounded-lg px-3 py-2.5 text-sm outline-none transition-all"
              style={{
                border: '1px solid #e5e7eb',
                color: '#111827',
                backgroundColor: '#f9fafb',
              }}
              onFocus={(e) => {
                e.target.style.borderColor = '#2563eb'
                e.target.style.backgroundColor = '#ffffff'
                e.target.style.boxShadow = '0 0 0 3px rgba(37,99,235,0.12)'
              }}
              onBlur={(e) => {
                e.target.style.borderColor = '#e5e7eb'
                e.target.style.backgroundColor = '#f9fafb'
                e.target.style.boxShadow = 'none'
              }}
            />
         </div>

         <div>
            <label className="mb-1.5 block text-sm font-medium" style={{ color: '#111827' }}>
               Include title text inside the image?
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <label 
                className="rounded-lg p-4 cursor-pointer flex items-center gap-3 transition-colors border"
                style={{
                  borderColor: includeText ? '#2563eb' : '#e5e7eb',
                  backgroundColor: includeText ? '#eff6ff' : '#f9fafb',
                }}
              >
                 <input 
                   type="radio" 
                   name="textInside" 
                   className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500" 
                   checked={includeText}
                   onChange={() => setIncludeText(true)}
                 />
                 <span className="text-sm font-medium" style={{ color: includeText ? '#1e40af' : '#374151' }}>Yes, include text overlay</span>
              </label>
              <label 
                className="rounded-lg p-4 cursor-pointer flex items-center gap-3 transition-colors border"
                style={{
                  borderColor: !includeText ? '#2563eb' : '#e5e7eb',
                  backgroundColor: !includeText ? '#eff6ff' : '#f9fafb',
                }}
              >
                 <input 
                   type="radio" 
                   name="textInside" 
                   className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500" 
                   checked={!includeText}
                   onChange={() => setIncludeText(false)}
                 />
                 <span className="text-sm font-medium" style={{ color: !includeText ? '#1e40af' : '#374151' }}>No, keep it visual only</span>
              </label>
            </div>
         </div>

         <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div>
               <label className="mb-1.5 block text-sm font-medium" style={{ color: '#111827' }}>
                  Reference image (Style guide)
               </label>
               <div 
                 className="rounded-lg border-2 border-dashed p-6 flex flex-col items-center justify-center text-center cursor-pointer h-32 transition-colors"
                 style={{
                   borderColor: '#d1d5db',
                   backgroundColor: '#f9fafb',
                 }}
                 onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#f3f4f6' }}
                 onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '#f9fafb' }}
               >
                  <UploadCloud className="w-6 h-6 mb-2" style={{ color: '#9ca3af' }} />
                  <div className="text-sm font-medium" style={{ color: '#374151' }}>Drop reference or click to browse</div>
                  <div className="text-xs mt-1" style={{ color: '#6b7280' }}>PNG, JPG up to 10MB</div>
               </div>
            </div>
            <div>
               <label className="mb-1.5 block text-sm font-medium" style={{ color: '#111827' }}>
                  Your asset (Face/product)
               </label>
               <div 
                 className="rounded-lg border-2 border-dashed p-6 flex flex-col items-center justify-center text-center cursor-pointer h-32 transition-colors"
                 style={{
                   borderColor: '#d1d5db',
                   backgroundColor: '#f9fafb',
                 }}
                 onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#f3f4f6' }}
                 onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '#f9fafb' }}
               >
                  <ImageIcon className="w-6 h-6 mb-2" style={{ color: '#9ca3af' }} />
                  <div className="text-sm font-medium" style={{ color: '#374151' }}>Upload main subject</div>
                  <div className="text-xs mt-1" style={{ color: '#6b7280' }}>Recommended: Transparent PNG</div>
               </div>
            </div>
         </div>

         <div>
            <label className="mb-1.5 block text-sm font-medium" style={{ color: '#111827' }}>
               AI generation engine
            </label>
            <div className="relative">
               <select 
                 className="w-full rounded-lg px-3 py-2.5 text-sm outline-none transition-all appearance-none cursor-pointer"
                 style={{
                   border: '1px solid #e5e7eb',
                   color: '#111827',
                   backgroundColor: '#f9fafb',
                 }}
                 onFocus={(e) => {
                   e.target.style.borderColor = '#2563eb'
                   e.target.style.backgroundColor = '#ffffff'
                   e.target.style.boxShadow = '0 0 0 3px rgba(37,99,235,0.12)'
                 }}
                 onBlur={(e) => {
                   e.target.style.borderColor = '#e5e7eb'
                   e.target.style.backgroundColor = '#f9fafb'
                   e.target.style.boxShadow = 'none'
                 }}
               >
                  <option>Dall-E 3 (High Precision)</option>
                  <option>Midjourney V6 (Artistic)</option>
               </select>
               <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none" style={{ color: '#6b7280' }} />
            </div>
         </div>
      </div>

      <div
        className="flex flex-wrap items-center justify-end gap-3 border-t px-5 py-4"
        style={{ borderColor: '#e5e7eb' }}
      >
        <button
          type="button"
          className="rounded-lg px-4 py-2 text-sm font-medium"
          style={{
            border: '1px solid #e5e7eb',
            color: '#374151',
            backgroundColor: '#ffffff',
          }}
        >
          Save as draft
        </button>
        <button
          type="submit"
          className="rounded-lg px-4 py-2 text-sm font-semibold text-white transition-all"
          style={{
            background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
            boxShadow: '0 1px 2px rgba(37,99,235,0.4), 0 4px 12px rgba(37,99,235,0.2)',
          }}
        >
          Generate Thumbnail
        </button>
      </div>
    </div>
  )
}
