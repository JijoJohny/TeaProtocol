import { useState, useEffect } from 'react'
import './Wallet.css'

const Wallet = () => {
  const [walletInfo, setWalletInfo] = useState({
    address: '0x123...abc',
    balance: 1000,
    isFrozen: false,
    lastUpdated: new Date().toISOString(),
  })

  // TODO: Implement real-time wallet data fetching
  useEffect(() => {
    // Fetch wallet data
  }, [])

  return (
    <div className="wallet-page">
      <div className="container">
        <div className="wallet-header">
          <h1>Wallet Dashboard</h1>
          <p>Manage your VUSD tokens and monitor your wallet status</p>
        </div>

        <div className="wallet-grid">
          {/* Balance Card */}
          <div className="wallet-card">
            <div className="balance-info">
              <h2>VUSD Balance</h2>
              <div className="balance-amount">{walletInfo.balance} VUSD</div>
              <div className="balance-change">
                <span className="change-arrow">↑</span>
                23.36% (30 days)
              </div>
            </div>
          </div>

          {/* Status Card */}
          <div className="wallet-card">
            <h2>Wallet Status</h2>
            <div className="status-info">
              <div className="status-item">
                <span className="status-label">Address</span>
                <span className="status-value">{walletInfo.address}</span>
              </div>
              <div className="status-item">
                <span className="status-label">Status</span>
                <span className={`status-badge ${walletInfo.isFrozen ? 'frozen' : 'active'}`}>
                  {walletInfo.isFrozen ? 'Frozen' : 'Active'}
                </span>
              </div>
              <div className="status-item">
                <span className="status-label">Last Updated</span>
                <span className="status-value">
                  {new Date(walletInfo.lastUpdated).toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="wallet-note">
          <p>
            Your wallet is connected to the Algorand network. All transactions are processed on-chain
            and can be verified on the Algorand blockchain explorer.
          </p>
        </div>
      </div>
    </div>
  )
}

export default Wallet 