import GameUI from './TangoGame'
import { Analytics } from '@vercel/analytics/react'

function App() {
  return (
    <div className="App">
      <GameUI />
      <Analytics />
    </div>
  )
}

export default App
