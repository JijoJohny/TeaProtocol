import { useState, useEffect } from 'react'
import './App.css'

const API_BASE = 'http://localhost:8000'; // Adjust if backend runs elsewhere

function App() {
  // State for Create Token
  const [tokenData, setTokenData] = useState({
    total_units: '',
    decimals: 2,
    asset_name: '',
    unit_name: '',
    metadata_url: ''
  });
  const [tokenResult, setTokenResult] = useState(null);
  const [tokenLoading, setTokenLoading] = useState(false);

  // State for Freeze/Unfreeze
  const [freezeAddress, setFreezeAddress] = useState('');
  const [freezeResult, setFreezeResult] = useState(null);
  const [freezeLoading, setFreezeLoading] = useState(false);
  const [unfreezeAddress, setUnfreezeAddress] = useState('');
  const [unfreezeResult, setUnfreezeResult] = useState(null);
  const [unfreezeLoading, setUnfreezeLoading] = useState(false);

  // State for Whitelist
  const [whitelistData, setWhitelistData] = useState({
    event_id: '',
    addresses: '', // comma separated
    action: 'add'
  });
  const [whitelistResult, setWhitelistResult] = useState(null);
  const [whitelistLoading, setWhitelistLoading] = useState(false);

  // State for Pool Status
  const [poolStatus, setPoolStatus] = useState(null);
  const [poolLoading, setPoolLoading] = useState(false);

  // State for Token Regeneration
  const [regenerateAddress, setRegenerateAddress] = useState('');
  const [regenerateResult, setRegenerateResult] = useState(null);
  const [regenerateLoading, setRegenerateLoading] = useState(false);

  // State for sidebar collapse
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // State for dark mode
  const [darkMode, setDarkMode] = useState(true);

  // State for PeraWallet
  const [peraWallet, setPeraWallet] = useState(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    // Check if PeraWallet is installed
    if (window.AlgoSigner) {
      setPeraWallet(window.AlgoSigner);
    } else {
      console.log('PeraWallet is not installed!');
    }
  }, []);

  const connectPeraWallet = async () => {
    if (peraWallet) {
      try {
        await peraWallet.connect();
        setConnected(true);
      } catch (error) {
        console.error('Failed to connect to PeraWallet:', error);
      }
    }
  };

  // Handlers
  const handleTokenChange = e => {
    setTokenData({ ...tokenData, [e.target.name]: e.target.value });
  };
  const handleCreateToken = async e => {
    e.preventDefault();
    setTokenLoading(true);
    setTokenResult(null);
    try {
      const res = await fetch(`${API_BASE}/admin/token/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...tokenData,
          total_units: Number(tokenData.total_units),
          decimals: Number(tokenData.decimals)
        })
      });
      const data = await res.json();
      setTokenResult(data);
    } catch (err) {
      setTokenResult({ error: 'Failed to create token' });
    }
    setTokenLoading(false);
  };

  const handleFreeze = async e => {
    e.preventDefault();
    setFreezeLoading(true);
    setFreezeResult(null);
    try {
      const res = await fetch(`${API_BASE}/admin/wallet/freeze/${freezeAddress}`, {
        method: 'POST'
      });
      const data = await res.json();
      setFreezeResult(data);
    } catch (err) {
      setFreezeResult({ error: 'Failed to freeze wallet' });
    }
    setFreezeLoading(false);
  };

  const handleUnfreeze = async e => {
    e.preventDefault();
    setUnfreezeLoading(true);
    setUnfreezeResult(null);
    try {
      const res = await fetch(`${API_BASE}/admin/wallet/unfreeze/${unfreezeAddress}`, {
        method: 'POST'
      });
      const data = await res.json();
      setUnfreezeResult(data);
    } catch (err) {
      setUnfreezeResult({ error: 'Failed to unfreeze wallet' });
    }
    setUnfreezeLoading(false);
  };

  const handleWhitelistChange = e => {
    setWhitelistData({ ...whitelistData, [e.target.name]: e.target.value });
  };
  const handleManageWhitelist = async e => {
    e.preventDefault();
    setWhitelistLoading(true);
    setWhitelistResult(null);
    try {
      const res = await fetch(`${API_BASE}/admin/whitelist/manage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...whitelistData,
          addresses: whitelistData.addresses.split(',').map(a => a.trim())
        })
      });
      const data = await res.json();
      setWhitelistResult(data);
    } catch (err) {
      setWhitelistResult({ error: 'Failed to manage whitelist' });
    }
    setWhitelistLoading(false);
  };

  const handleCheckPool = async () => {
    setPoolLoading(true);
    setPoolStatus(null);
    try {
      const res = await fetch(`${API_BASE}/admin/pool/status`);
      const data = await res.json();
      setPoolStatus(data);
    } catch (err) {
      setPoolStatus({ error: 'Failed to fetch pool status' });
    }
    setPoolLoading(false);
  };

  const handleRegenerateToken = async e => {
    e.preventDefault();
    setRegenerateLoading(true);
    setRegenerateResult(null);
    try {
      const res = await fetch(`${API_BASE}/admin/token/regenerate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_address: regenerateAddress })
      });
      const data = await res.json();
      setRegenerateResult(data);
    } catch (err) {
      setRegenerateResult({ error: 'Failed to regenerate token' });
    }
    setRegenerateLoading(false);
  };

  const toggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  return (
    <div className={`dashboard-layout ${darkMode ? 'dark-mode' : ''}`}>
      <header className="dashboard-header">
        <h1>Admin Dashboard</h1>
        <button onClick={toggleDarkMode}>{darkMode ? 'Light Mode' : 'Dark Mode'}</button>
        <button onClick={connectPeraWallet} disabled={connected}>{connected ? 'Connected' : 'Connect PeraWallet'}</button>
      </header>
      <div className="dashboard-content">
        <aside className={`dashboard-sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
          <button onClick={toggleSidebar}>{sidebarCollapsed ? '>' : '<'}</button>
          <nav>
            <ul>
              <li><a href="#create-token">Create Token</a></li>
              <li><a href="#freeze-wallet">Freeze Wallet</a></li>
              <li><a href="#unfreeze-wallet">Unfreeze Wallet</a></li>
              <li><a href="#manage-whitelist">Manage Whitelist</a></li>
              <li><a href="#pool-status">Pool Status</a></li>
              <li><a href="#regenerate-token">Regenerate Token</a></li>
            </ul>
          </nav>
        </aside>
        <main className="dashboard-main">
          <section id="create-token" className="dashboard-section">
            <h2>Create Token</h2>
            <form onSubmit={handleCreateToken}>
              <label>Asset Name: <input name="asset_name" placeholder="Enter Asset Name" value={tokenData.asset_name} onChange={handleTokenChange} required /></label>
              <label>Unit Name: <input name="unit_name" placeholder="Enter Unit Name" value={tokenData.unit_name} onChange={handleTokenChange} required /></label>
              <label>Total Units: <input name="total_units" placeholder="Enter Total Units" type="number" value={tokenData.total_units} onChange={handleTokenChange} required /></label>
              <label>Decimals: <input name="decimals" placeholder="Enter Decimals" type="number" value={tokenData.decimals} onChange={handleTokenChange} required /></label>
              <label>Metadata URL: <input name="metadata_url" placeholder="Enter Metadata URL" value={tokenData.metadata_url} onChange={handleTokenChange} /></label>
              <button type="submit" disabled={tokenLoading}>{tokenLoading ? 'Creating...' : 'Create Token'}</button>
            </form>
            {tokenResult && <pre>{JSON.stringify(tokenResult, null, 2)}</pre>}
          </section>

          <section id="freeze-wallet" className="dashboard-section">
            <h2>Freeze Wallet</h2>
            <form onSubmit={handleFreeze}>
              <label>Wallet Address: <input placeholder="Enter Wallet Address" value={freezeAddress} onChange={e => setFreezeAddress(e.target.value)} required /></label>
              <button type="submit" disabled={freezeLoading}>{freezeLoading ? 'Freezing...' : 'Freeze'}</button>
            </form>
            {freezeResult && <pre>{JSON.stringify(freezeResult, null, 2)}</pre>}
          </section>

          <section id="unfreeze-wallet" className="dashboard-section">
            <h2>Unfreeze Wallet</h2>
            <form onSubmit={handleUnfreeze}>
              <label>Wallet Address: <input placeholder="Enter Wallet Address" value={unfreezeAddress} onChange={e => setUnfreezeAddress(e.target.value)} required /></label>
              <button type="submit" disabled={unfreezeLoading}>{unfreezeLoading ? 'Unfreezing...' : 'Unfreeze'}</button>
            </form>
            {unfreezeResult && <pre>{JSON.stringify(unfreezeResult, null, 2)}</pre>}
          </section>

          <section id="manage-whitelist" className="dashboard-section">
            <h2>Manage Whitelist</h2>
            <form onSubmit={handleManageWhitelist}>
              <label>Event ID: <input name="event_id" placeholder="Enter Event ID" value={whitelistData.event_id} onChange={handleWhitelistChange} required /></label>
              <label>Addresses: <input name="addresses" placeholder="Enter Addresses (comma separated)" value={whitelistData.addresses} onChange={handleWhitelistChange} required /></label>
              <label>Action: <select name="action" value={whitelistData.action} onChange={handleWhitelistChange}>
                <option value="add">Add</option>
                <option value="remove">Remove</option>
              </select></label>
              <button type="submit" disabled={whitelistLoading}>{whitelistLoading ? 'Processing...' : 'Manage Whitelist'}</button>
            </form>
            {whitelistResult && <pre>{JSON.stringify(whitelistResult, null, 2)}</pre>}
          </section>

          <section id="pool-status" className="dashboard-section">
            <h2>Check Pool Status</h2>
            <button onClick={handleCheckPool} disabled={poolLoading}>{poolLoading ? 'Checking...' : 'Check Pool Status'}</button>
            {poolStatus && <pre>{JSON.stringify(poolStatus, null, 2)}</pre>}
          </section>

          <section id="regenerate-token" className="dashboard-section">
            <h2>Regenerate Token</h2>
            <form onSubmit={handleRegenerateToken}>
              <label>User Address: <input placeholder="Enter User Address" value={regenerateAddress} onChange={e => setRegenerateAddress(e.target.value)} required /></label>
              <button type="submit" disabled={regenerateLoading}>{regenerateLoading ? 'Regenerating...' : 'Regenerate Token'}</button>
            </form>
            {regenerateResult && <pre>{JSON.stringify(regenerateResult, null, 2)}</pre>}
          </section>
        </main>
      </div>
      </div>
  )
}

export default App
