import { useState } from 'react'
import './InputBox.css'

export default function InputBox({ onSendMessage, isConnected, isTyping }) {
  const [message, setMessage] = useState('')

  const submit = (event) => {
    event.preventDefault()
    const clean = message.trim()
    if (!clean || !isConnected || isTyping) return
    onSendMessage(clean)
    setMessage('')
  }

  return (
    <form className="input-container" onSubmit={submit}>
      <textarea
        className="message-input"
        value={message}
        maxLength={2000}
        rows={1}
        placeholder={isConnected ? 'Message SmartStay AI…' : 'Waiting for the local server…'}
        disabled={!isConnected || isTyping}
        onChange={(event) => setMessage(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === 'Enter' && !event.shiftKey) submit(event)
        }}
      />
      <button className="send-button" type="submit" disabled={!message.trim() || !isConnected || isTyping}>
        Send
      </button>
    </form>
  )
}

