import { useEffect, useMemo, useRef, useState } from 'react'

interface Props {
  label: string
  files: File[]
  onChange: (files: File[]) => void
  multiple?: boolean
}

/** Controlled drag-and-drop / click-to-browse image picker.
 *
 * The parent owns the file list: previews always mirror `files`, each one has
 * a remove button, and clearing `files` after submit clears the previews too.
 */
export default function ImageDropzone({ label, files, onChange, multiple = true }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragOver, setDragOver] = useState(false)

  const previews = useMemo(() => files.map((f) => URL.createObjectURL(f)), [files])
  useEffect(
    () => () => previews.forEach((url) => URL.revokeObjectURL(url)),
    [previews],
  )

  const accept = (list: FileList | null) => {
    if (!list?.length) return
    const images = Array.from(list).filter((f) => f.type.startsWith('image/'))
    if (!images.length) return
    onChange(multiple ? [...files, ...images] : images.slice(0, 1))
  }

  const removeAt = (index: number) => onChange(files.filter((_, i) => i !== index))

  return (
    <div>
      <div
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault()
          setDragOver(true)
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragOver(false)
          accept(e.dataTransfer.files)
        }}
        className={`cursor-pointer rounded-xl border-2 border-dashed p-8 text-center text-sm transition ${
          dragOver
            ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
            : 'border-slate-300 bg-white text-slate-500 hover:border-indigo-400'
        }`}
      >
        {label}
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          multiple={multiple}
          hidden
          onChange={(e) => {
            accept(e.target.files)
            e.target.value = ''
          }}
        />
      </div>
      {previews.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {previews.map((src, i) => (
            <div key={i} className="group relative">
              <img src={src} className="h-16 w-16 rounded-lg object-cover" />
              <button
                type="button"
                title="remove"
                onClick={(e) => {
                  e.stopPropagation()
                  removeAt(i)
                }}
                className="absolute -right-1.5 -top-1.5 hidden h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs font-bold text-white shadow group-hover:flex"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
