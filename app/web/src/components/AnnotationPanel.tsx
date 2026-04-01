import { useState } from 'react'
import type { Annotation } from '@/types/garment'
import { useAnnotations } from '@/hooks/useAnnotations'

interface Props {
  garmentId: number
  onChange?: () => void
}

export function AnnotationPanel({ garmentId, onChange }: Props) {
  const { annotations, loading, add, remove } = useAnnotations(garmentId)
  const [tagInput, setTagInput] = useState('')
  const [notesInput, setNotesInput] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const parseTags = (raw: string) =>
    raw
      .split(/[,\s]+/)
      .map(t => t.trim().toLowerCase())
      .filter(Boolean)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!tagInput.trim() && !notesInput.trim()) return
    setSubmitting(true)
    try {
      await add(parseTags(tagInput), notesInput)
      setTagInput('')
      setNotesInput('')
      onChange?.()
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id: number) => {
    await remove(id)
    onChange?.()
  }

  return (
    <div className="space-y-3">
      {/* Existing annotations */}
      {loading ? (
        <div className="text-xs text-amber-500 animate-pulse">Loading…</div>
      ) : annotations.length === 0 ? (
        <p className="text-xs text-gray-400 italic">No annotations yet.</p>
      ) : (
        <ul className="space-y-2">
          {annotations.map(a => (
            <AnnotationItem key={a.id} annotation={a} onDelete={() => handleDelete(a.id)} />
          ))}
        </ul>
      )}

      {/* Add annotation form */}
      <form onSubmit={handleSubmit} className="space-y-2 pt-2 border-t border-amber-100">
        <input
          type="text"
          placeholder="Tags (comma-separated): flowy, artisan, resort"
          value={tagInput}
          onChange={e => setTagInput(e.target.value)}
          className="w-full border border-gray-200 rounded px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-amber-400"
        />
        <textarea
          placeholder="Your observation or note…"
          value={notesInput}
          onChange={e => setNotesInput(e.target.value)}
          rows={2}
          className="w-full border border-gray-200 rounded px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-amber-400 resize-none"
        />
        <button
          type="submit"
          disabled={submitting}
          className="text-xs bg-amber-500 hover:bg-amber-600 disabled:opacity-50 text-white px-3 py-1.5 rounded transition-colors"
        >
          {submitting ? 'Saving…' : '+ Add Note'}
        </button>
      </form>
    </div>
  )
}

function AnnotationItem({
  annotation,
  onDelete,
}: {
  annotation: Annotation
  onDelete: () => void
}) {
  return (
    <li className="text-xs space-y-1 group relative">
      {annotation.tags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {annotation.tags.map(t => (
            <span
              key={t}
              className="bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded-full capitalize"
            >
              #{t}
            </span>
          ))}
        </div>
      )}
      {annotation.notes && <p className="text-gray-600 leading-relaxed">{annotation.notes}</p>}
      <p className="text-gray-400">{new Date(annotation.createdAt).toLocaleDateString()}</p>
      <button
        onClick={onDelete}
        className="absolute top-0 right-0 hidden group-hover:block text-gray-300 hover:text-red-500 text-xs"
      >
        ✕
      </button>
    </li>
  )
}
