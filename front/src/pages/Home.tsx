import { useNavigate } from 'react-router-dom'
import { FaWallet, FaHistory, FaMoneyBillWave } from 'react-icons/fa'
import './Home.css'

const Feature = ({ icon: Icon, title, text }: { icon: any; title: string; text: string }) => {
  return (
    <div className="feature-card">
      <Icon className="feature-icon" />
      <h3>{title}</h3>
      <p>{text}</p>
    </div>
  )
}

const Home = () => {
  const navigate = useNavigate()

  return (
    <div className="home">
      {/* Hero Section */}
      <section className="hero">
        <div className="container">
          <div className="hero-content">
            <h1>Welcome to AlgoHack</h1>
            <p>
              The decentralized lending platform built on Algorand. Borrow VUSD tokens securely and efficiently.
            </p>
            <button className="btn btn-primary" onClick={() => navigate('/borrow')}>
              Start Borrowing
            </button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features">
        <div className="container">
          <div className="features-grid">
            <Feature
              icon={FaWallet}
              title="Secure Wallet Integration"
              text="Connect your Pera wallet securely and manage your VUSD tokens with ease."
            />
            <Feature
              icon={FaMoneyBillWave}
              title="Instant Borrowing"
              text="Borrow VUSD tokens instantly with our streamlined lending process."
            />
            <Feature
              icon={FaHistory}
              title="Transaction History"
              text="Track all your borrowing activities with detailed transaction history."
            />
          </div>
        </div>
      </section>
    </div>
  )
}

export default Home 