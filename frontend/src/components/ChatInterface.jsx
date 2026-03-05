import MessageDisplay from './MessageDisplay'
import InputBox from './InputBox'
import './ChatInterface.css'

export default function ChatInterface({
  messages,
  onSendMessage,
  onReconnect,
  isConnected,
  isTyping,
  connectionError,
}) {
  return (
    <main className="chat-interface">
      {connectionError && (
        <div className="connection-error">
          <span>{connectionError}</span>
          <button className="reconnect-button" onClick={onReconnect}>Reconnect</button>
        </div>
      )}
      <div className="chat-container">
        <MessageDisplay messages={messages} isTyping={isTyping} />
        <InputBox onSendMessage={onSendMessage} isConnected={isConnected} isTyping={isTyping} />
      </div>
    </main>
  )
}

