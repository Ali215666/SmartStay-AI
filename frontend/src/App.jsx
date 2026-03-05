import { useEffect, useRef, useState } from 'react'
import ChatInterface from './components/ChatInterface'
import websocketService from './utils/websocketService'
import './App.css'

const newSessionId = () => crypto.randomUUID()
const stamp = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

function App() {
  const [sessionId, setSessionId] = useState(newSessionId)
  const [messages, setMessages] = useState([])
  const [isConnected, setConnected] = useState(false)
  const [isTyping, setTyping] = useState(false)
  const [error, setError] = useState('')
  const streamingId = useRef(null)

  const connect = () => {
    setError('')
    websocketService.connect(import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/chat')
  }

  useEffect(() => {
    websocketService.onConnect(() => setConnected(true))
    websocketService.onDisconnect(() => setConnected(false))
    websocketService.onError((message) => {
      setError(message)
      setTyping(false)
    })
    websocketService.onStreamToken((token) => {
      setMessages((current) => {
        const next = [...current]
        const index = next.findIndex((message) => message.id === streamingId.current)
        if (index >= 0) next[index] = { ...next[index], content: next[index].content + token }
        return next
      })
    })
    websocketService.onMessage(({ type }) => {
      if (type === 'end') {
        setTyping(false)
        streamingId.current = null
      }
    })
    connect()
    return () => websocketService.disconnect()
  }, [])

  const sendMessage = (content) => {
    const assistantId = crypto.randomUUID()
    const sent = websocketService.send({ session_id: sessionId, message: content })
    if (!sent) {
      setError('Not connected to the SmartStay API.')
      return
    }
    streamingId.current = assistantId
    setMessages((current) => [
      ...current,
      { id: crypto.randomUUID(), role: 'user', content, timestamp: stamp() },
      { id: assistantId, role: 'assistant', content: '', timestamp: stamp() },
    ])
    setTyping(true)
  }

  const reset = () => {
    setSessionId(newSessionId())
    setMessages([])
    setTyping(false)
    streamingId.current = null
  }

  return (
    <div className="app">
      <header className="app-header">
        <button className="new-session-button" onClick={reset}>New chat</button>
        <h1 className="app-title">SmartStay AI</h1>
        <div className="connection-status">
          <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`} />
          {isConnected ? 'Connected' : 'Disconnected'}
        </div>
      </header>
      <ChatInterface
        messages={messages}
        onSendMessage={sendMessage}
        onReconnect={connect}
        isConnected={isConnected}
        isTyping={isTyping}
        connectionError={error}
      />
    </div>
  )
}

export default App

