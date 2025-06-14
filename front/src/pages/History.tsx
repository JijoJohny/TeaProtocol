import { useState, useEffect } from 'react'
import './History.css'

interface Transaction {
  id: string
  amount: number
  date: string
  status: 'completed' | 'pending' | 'failed'
  type: 'borrow' | 'repay'
}

const History = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([
    {
      id: '1',
      amount: 1000,
      date: '2024-03-15T10:30:00Z',
      status: 'completed',
      type: 'borrow',
    },
    {
      id: '2',
      amount: 500,
      date: '2024-03-14T15:45:00Z',
      status: 'completed',
      type: 'repay',
    },
    // Add more sample transactions
  ])

  // TODO: Implement real-time transaction history fetching
  useEffect(() => {
    // Fetch transaction history
  }, [])

  const getStatusClass = (status: string) => {
    switch (status) {
      case 'completed':
        return 'status-success'
      case 'pending':
        return 'status-warning'
      case 'failed':
        return 'status-error'
      default:
        return ''
    }
  }

  return (
    <div className="history-page">
      <div className="container">
        <div className="history-header">
          <h1>Transaction History</h1>
          <p>View all your borrowing and repayment transactions</p>
        </div>

        <div className="history-table-container">
          <table className="history-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Type</th>
                <th>Amount (VUSD)</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((tx) => (
                <tr key={tx.id}>
                  <td>{new Date(tx.date).toLocaleString()}</td>
                  <td>
                    <span className={`transaction-type ${tx.type}`}>
                      {tx.type === 'borrow' ? 'Borrow' : 'Repay'}
                    </span>
                  </td>
                  <td className="amount">{tx.amount}</td>
                  <td>
                    <span className={`status-badge ${getStatusClass(tx.status)}`}>
                      {tx.status.charAt(0).toUpperCase() + tx.status.slice(1)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {transactions.length === 0 && (
          <div className="no-transactions">
            <p>No transactions found</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default History 