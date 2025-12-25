import { Loader2 } from 'lucide-react'

export default function LoadingSpinner({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-4">
      <Loader2 className="w-12 h-12 text-primary-500 animate-spin" />
      <p className="text-gray-400">{message}</p>
    </div>
  )
}
