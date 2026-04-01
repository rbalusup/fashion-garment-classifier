import { useCallback, useRef } from 'react'

interface Props {
  onSearch: (q: string) => void
}

export function SearchBar({ onSearch }: Props) {
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (timer.current) clearTimeout(timer.current)
      timer.current = setTimeout(() => onSearch(e.target.value), 300)
    },
    [onSearch]
  )

  return (
    <input
      type="search"
      placeholder='Search descriptions, trends… e.g. "embroidered neckline"'
      onChange={handleChange}
      className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
    />
  )
}
