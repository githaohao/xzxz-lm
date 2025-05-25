import StreamingChat from '@/components/streaming-chat'
import Navigation from '@/components/ui/navigation'

export default function Home() {
  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-4">
        <Navigation />
        <StreamingChat />
      </div>
    </div>
  )
} 