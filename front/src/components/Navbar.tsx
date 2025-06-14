import { Link } from 'react-router-dom'
import { useState } from 'react'
import './Navbar.css'

const Navbar = () => {
  const [isConnected, setIsConnected] = useState(false)
  const [walletAddress, setWalletAddress] = useState('')

  const connectWallet = async () => {
    // TODO: Implement wallet connection logic
    setIsConnected(true)
    setWalletAddress('0x123...abc')
  }

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div className="navbar-links">
          <Link to="/" className="navbar-link">Home</Link>
          <Link to="/borrow" className="navbar-link">Borrow</Link>
          <Link to="/wallet" className="navbar-link">Wallet</Link>
          <Link to="/history" className="navbar-link">History</Link>
        </div>
        
        <div className="navbar-wallet">
          {isConnected ? (
            <span className="wallet-address">{walletAddress}</span>
          ) : (
            <button className="btn btn-primary" onClick={connectWallet}>
              Connect Wallet
            </button>
          )}
        </div>
      </div>
    </nav>
  )
}

export default Navbar 