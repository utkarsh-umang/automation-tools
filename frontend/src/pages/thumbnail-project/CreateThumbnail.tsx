import Uppy from '@uppy/core'
import DashboardPlugin from '@uppy/dashboard'
import { ChevronDown } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import {
  getApiErrorMessage,
  useCreateThumbnailMutation,
} from '@/hooks/api/useThumbnailApi'
import {
  useCreateFolderMutation,
  useFolderListQuery,
  useUpdateFolderMutation,
} from '@/hooks/api/useFolderApi'

import '@uppy/core/css/style.min.css'
import '@uppy/dashboard/css/style.min.css'

const MAX_BYTES = 10 * 1024 * 1024

// Flux Kontext first (and default) — cheapest per-generation, use it first and
// only reach for the pricier models below if a result doesn't look right.
const MODEL_OPTIONS = [
  { value: 'fluxkontext', label: 'Flux Kontext (cheapest — try first)' },
  { value: 'gptimage', label: 'GPT Image' },
  { value: 'nanobanana', label: 'Nano Banana' },
] as const

const NO_FOLDER = ''
const NEW_FOLDER = '__new__'

type CreateThumbnailProps = {
  onCreated?: () => void
}

export function CreateThumbnail({ onCreated }: CreateThumbnailProps) {
  const [title, setTitle] = useState('')
  const [includeText, setIncludeText] = useState(true)
  const [creativeComments, setCreativeComments] = useState('')
  const [model, setModel] = useState<(typeof MODEL_OPTIONS)[number]['value']>('fluxkontext')
  const [formError, setFormError] = useState<string | null>(null)

  const { data: folderData } = useFolderListQuery()
  const folders = folderData?.folders ?? []
  const [folderSelection, setFolderSelection] = useState<string>(NO_FOLDER)
  const [newFolderName, setNewFolderName] = useState('')
  const [newFolderStyle, setNewFolderStyle] = useState('')
  const [editingStyle, setEditingStyle] = useState('')
  const [editingStyleDirty, setEditingStyleDirty] = useState(false)
  const createFolderMutation = useCreateFolderMutation()
  const updateFolderMutation = useUpdateFolderMutation()

  const selectedFolder = folders.find((f) => f.id === folderSelection)

  useEffect(() => {
    setEditingStyle(selectedFolder?.style_prompt ?? '')
    setEditingStyleDirty(false)
  }, [selectedFolder?.id, selectedFolder?.style_prompt])

  async function handleCreateFolder() {
    if (!newFolderName.trim()) return
    const folder = await createFolderMutation.mutateAsync({
      name: newFolderName.trim(),
      style_prompt: newFolderStyle.trim(),
    })
    setFolderSelection(folder.id)
    setNewFolderName('')
    setNewFolderStyle('')
  }

  async function handleSaveFolderStyle() {
    if (!selectedFolder) return
    await updateFolderMutation.mutateAsync({
      folderId: selectedFolder.id,
      body: { style_prompt: editingStyle },
    })
    setEditingStyleDirty(false)
  }

  const referenceContainerRef = useRef<HTMLDivElement>(null)
  const baseContainerRef = useRef<HTMLDivElement>(null)
  // Uppy instances are created in useEffect (after DOM is painted) so the ResizeObserver
  // always starts on a fully laid-out element, preventing the blank-Dashboard flash.
  const referenceUppyRef = useRef<Uppy | null>(null)
  const baseUppyRef = useRef<Uppy | null>(null)

  useEffect(() => {
    const refUppy = new Uppy({
      id: 'thumbnail-reference',
      restrictions: { maxNumberOfFiles: 1, maxFileSize: MAX_BYTES, allowedFileTypes: ['image/*'] },
    })
    refUppy.use(DashboardPlugin, {
      id: 'ReferenceDashboard',
      target: referenceContainerRef.current!,
      inline: true,
      height: 260,
      proudlyDisplayPoweredByUppy: false,
      hideUploadButton: true,
    })
    referenceUppyRef.current = refUppy

    const baseUppy = new Uppy({
      id: 'thumbnail-base',
      restrictions: { maxNumberOfFiles: 20, maxFileSize: MAX_BYTES, allowedFileTypes: ['image/*'] },
    })
    baseUppy.use(DashboardPlugin, {
      id: 'BaseDashboard',
      target: baseContainerRef.current!,
      inline: true,
      height: 260,
      proudlyDisplayPoweredByUppy: false,
      hideUploadButton: true,
    })
    baseUppyRef.current = baseUppy

    return () => {
      refUppy.destroy()
      baseUppy.destroy()
      referenceUppyRef.current = null
      baseUppyRef.current = null
    }
  }, [])

  const createMutation = useCreateThumbnailMutation()

  async function handleGenerate() {
    setFormError(null)
    const refUppy = referenceUppyRef.current
    const baseUppy = baseUppyRef.current

    const refFiles = refUppy?.getFiles() ?? []
    const ref = refFiles[0]
    if (!ref) {
      setFormError('Add a reference image (style guide).')
      return
    }
    if (!title.trim()) {
      setFormError('Enter a thumbnail title.')
      return
    }

    const baseBlobs = (baseUppy?.getFiles() ?? []).map((f) => f.data as Blob)

    try {
      await createMutation.mutateAsync({
        reference_image: ref.data as Blob,
        base_images: baseBlobs.length ? baseBlobs : undefined,
        title: title.trim(),
        include_title: includeText,
        creative_comments: creativeComments,
        model,
        folder_id: folderSelection && folderSelection !== NEW_FOLDER ? folderSelection : undefined,
      })
      refUppy?.cancelAll()
      baseUppy?.cancelAll()
      setTitle('')
      setCreativeComments('')
      onCreated?.()
    } catch (e) {
      setFormError(getApiErrorMessage(e))
    }
  }

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
            Client folder (optional)
          </label>
          <select
            value={folderSelection}
            onChange={(e) => setFolderSelection(e.target.value)}
            className="w-full rounded-lg px-3 py-2.5 text-sm outline-none transition-all"
            style={{ border: '1px solid #e5e7eb', color: '#111827', backgroundColor: '#f9fafb' }}
          >
            <option value={NO_FOLDER}>No folder</option>
            {folders.map((f) => (
              <option key={f.id} value={f.id}>
                {f.name}
              </option>
            ))}
            <option value={NEW_FOLDER}>+ New folder…</option>
          </select>
          <p className="mt-1 text-xs" style={{ color: '#6b7280' }}>
            Folders are shared with the whole team — a folder's style note is added to
            every thumbnail created inside it, so a client's preferred look travels with
            the client, not just with you.
          </p>

          {folderSelection === NEW_FOLDER && (
            <div
              className="mt-3 space-y-2.5 rounded-lg p-3.5"
              style={{ border: '1px dashed #d1d5db', backgroundColor: '#f9fafb' }}
            >
              <input
                type="text"
                value={newFolderName}
                onChange={(e) => setNewFolderName(e.target.value)}
                placeholder="Client name"
                className="w-full rounded-lg px-3 py-2 text-sm outline-none"
                style={{ border: '1px solid #e5e7eb', color: '#111827', backgroundColor: '#ffffff' }}
              />
              <textarea
                value={newFolderStyle}
                onChange={(e) => setNewFolderStyle(e.target.value)}
                rows={2}
                placeholder="Client's preferred visual style, always applied to their thumbnails…"
                className="w-full rounded-lg px-3 py-2 text-sm outline-none resize-y"
                style={{ border: '1px solid #e5e7eb', color: '#111827', backgroundColor: '#ffffff' }}
              />
              <button
                type="button"
                onClick={() => void handleCreateFolder()}
                disabled={!newFolderName.trim() || createFolderMutation.isPending}
                className="rounded-lg px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50"
                style={{ backgroundColor: '#2563eb' }}
              >
                {createFolderMutation.isPending ? 'Creating…' : 'Create folder'}
              </button>
            </div>
          )}

          {selectedFolder && (
            <div
              className="mt-3 space-y-2 rounded-lg p-3.5"
              style={{ border: '1px solid #e5e7eb', backgroundColor: '#f9fafb' }}
            >
              <label className="block text-xs font-medium" style={{ color: '#374151' }}>
                {selectedFolder.name}'s style note (shared — editing this changes it for everyone)
              </label>
              <textarea
                value={editingStyle}
                onChange={(e) => {
                  setEditingStyle(e.target.value)
                  setEditingStyleDirty(true)
                }}
                rows={2}
                className="w-full rounded-lg px-3 py-2 text-sm outline-none resize-y"
                style={{ border: '1px solid #e5e7eb', color: '#111827', backgroundColor: '#ffffff' }}
              />
              {editingStyleDirty && (
                <button
                  type="button"
                  onClick={() => void handleSaveFolderStyle()}
                  disabled={updateFolderMutation.isPending}
                  className="rounded-lg px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50"
                  style={{ backgroundColor: '#2563eb' }}
                >
                  {updateFolderMutation.isPending ? 'Saving…' : 'Save style note'}
                </button>
              )}
            </div>
          )}
        </div>

        <div>
          <label className="mb-1.5 block text-sm font-medium" style={{ color: '#111827' }}>
            Thumbnail title <span style={{ color: '#be123c' }}>*</span>
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
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
            Creative notes (optional)
          </label>
          <textarea
            value={creativeComments}
            onChange={(e) => setCreativeComments(e.target.value)}
            rows={3}
            placeholder="Direction for the model, brand constraints, etc."
            className="w-full rounded-lg px-3 py-2.5 text-sm outline-none transition-all resize-y min-h-[80px]"
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
              <span className="text-sm font-medium" style={{ color: includeText ? '#1e40af' : '#374151' }}>
                Yes, include text overlay
              </span>
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
              <span className="text-sm font-medium" style={{ color: !includeText ? '#1e40af' : '#374151' }}>
                No, keep it visual only
              </span>
            </label>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <div>
            <label className="mb-1.5 block text-sm font-medium" style={{ color: '#111827' }}>
              Reference image (style guide) <span style={{ color: '#be123c' }}>*</span>
            </label>
            <div
              className="rounded-lg overflow-hidden border border-dashed"
              style={{ borderColor: '#d1d5db', minHeight: 260 }}
            >
              <div ref={referenceContainerRef} />
            </div>
            <p className="mt-1 text-xs" style={{ color: '#6b7280' }}>
              One image, PNG/JPG/WebP up to 10MB.
            </p>
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium" style={{ color: '#111827' }}>
              Your assets (face / product)
            </label>
            <div
              className="rounded-lg overflow-hidden border border-dashed"
              style={{ borderColor: '#d1d5db', minHeight: 260 }}
            >
              <div ref={baseContainerRef} />
            </div>
            <p className="mt-1 text-xs" style={{ color: '#6b7280' }}>
              Optional. Multiple images allowed; transparent PNG recommended.
            </p>
          </div>
        </div>

        <div>
          <label className="mb-1.5 block text-sm font-medium" style={{ color: '#111827' }}>
            AI generation engine
          </label>
          <div className="relative">
            <select
              value={model}
              onChange={(e) => setModel(e.target.value as (typeof MODEL_OPTIONS)[number]['value'])}
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
              {MODEL_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <ChevronDown
              className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none"
              style={{ color: '#6b7280' }}
            />
          </div>
        </div>

        {formError && (
          <p className="text-sm text-red-600" role="alert">
            {formError}
          </p>
        )}
      </div>

      <div
        className="flex flex-wrap items-center justify-end gap-3 border-t px-5 py-4"
        style={{ borderColor: '#e5e7eb' }}
      >
        <button
          type="button"
          className="rounded-lg px-4 py-2 text-sm font-semibold text-white transition-all disabled:opacity-60"
          style={{
            background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
            boxShadow: '0 1px 2px rgba(37,99,235,0.4), 0 4px 12px rgba(37,99,235,0.2)',
          }}
          disabled={createMutation.isPending}
          onClick={() => void handleGenerate()}
        >
          {createMutation.isPending ? 'Submitting…' : 'Generate Thumbnail'}
        </button>
      </div>
    </div>
  )
}
