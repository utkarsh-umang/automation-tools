import { X, CheckCircle2, Sparkles, Download, MoreHorizontal } from 'lucide-react'

export function ThumbnailDetailModal({ thumbnail, onClose }: { thumbnail: any, onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-[#0f1f4a]/60 backdrop-blur-md p-4 sm:p-8 animate-in fade-in duration-200">
      <div className="bg-white rounded-[2rem] shadow-2xl max-w-5xl w-full flex flex-col md:flex-row overflow-hidden max-h-[90vh] ring-1 ring-white/20">
        {/* Left Side: Image */}
        <div className="w-full md:w-[60%] bg-[#0a0f1e] p-8 md:p-12 flex items-center justify-center relative overflow-hidden">
          <div className="absolute inset-0 opacity-20 bg-[radial-gradient(circle_at_center,rgba(37,99,235,0.8)_0%,transparent_100%)]"></div>
          <img 
             src={thumbnail.image} 
             alt="Thumbnail preview" 
             className="relative z-10 rounded-2xl shadow-2xl ring-1 ring-white/10 max-h-full max-w-full object-contain"
          />
        </div>

        {/* Right Side: Details */}
        <div className="w-full md:w-[40%] p-8 md:p-10 flex flex-col overflow-y-auto">
          <div className="flex justify-between items-start mb-8">
            <div>
              <div className="text-blue-600 text-xs font-black tracking-widest mb-1.5 uppercase">Project Details</div>
              <h2 className="text-[22px] font-bold text-gray-900 leading-tight pr-4">{thumbnail.title}</h2>
            </div>
            <button onClick={onClose} className="p-2.5 bg-gray-50 hover:bg-gray-100 rounded-full text-gray-500 transition-colors shrink-0">
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="space-y-6 flex-1">
            <div>
               <label className="block text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2.5">Original Title</label>
               <div className="bg-[#f8faff] text-[#0f1f4a] p-4 rounded-2xl font-semibold border border-blue-100/50 leading-relaxed text-[15px]">
                 Why Everyone is Learning AI Wrong: A Comprehensive Guide
               </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
               <div>
                  <label className="block text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2.5">Title Inside Image</label>
                  <div className="bg-[#f8faff] text-[#0f1f4a] p-3.5 rounded-2xl font-bold border border-blue-100/50 flex items-center gap-2">
                     <CheckCircle2 className="w-5 h-5 text-blue-600" /> Yes
                  </div>
               </div>
               <div>
                  <label className="block text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2.5">AI Model</label>
                  <div className="bg-[#f8faff] text-[#0f1f4a] p-3.5 rounded-2xl font-bold border border-blue-100/50 flex items-center gap-2">
                     <Sparkles className="w-4 h-4 text-purple-600" /> Dall-E 3
                  </div>
               </div>
            </div>

            <div>
               <label className="block text-[11px] font-black text-gray-400 uppercase tracking-widest mb-2.5">Visual Style</label>
               <div className="bg-[#f8faff] p-4 rounded-2xl border border-blue-100/50 flex flex-wrap gap-2.5">
                  <span className="bg-blue-100/60 text-blue-800 px-3 py-1.5 rounded-xl text-sm font-bold">Cyberpunk</span>
                  <span className="bg-blue-100/60 text-blue-800 px-3 py-1.5 rounded-xl text-sm font-bold">High Contrast</span>
                  <span className="bg-blue-100/60 text-blue-800 px-3 py-1.5 rounded-xl text-sm font-bold">Neo-Brutalism</span>
               </div>
            </div>
          </div>

          <div className="mt-8 pt-8 border-t border-gray-100 flex gap-4">
             <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 px-4 rounded-2xl shadow-[0_8px_20px_-4px_rgba(37,99,235,0.4)] transition-all flex items-center justify-center gap-2.5 active:scale-[0.98]">
                <Download className="w-5 h-5" /> Download 4K
             </button>
             <button className="p-4 bg-gray-50 hover:bg-gray-100 border border-gray-200/50 text-gray-600 rounded-2xl transition-colors">
                <MoreHorizontal className="w-6 h-6" />
             </button>
          </div>
        </div>
      </div>
    </div>
  )
}
