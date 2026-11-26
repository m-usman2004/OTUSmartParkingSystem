
import { useCallback, useEffect, useState } from 'react'
import './App.css'

const PRIMARY_API = '/api'
const BACKUP_API = '/backup-api'
const LOT_IDS = ['A', 'B', 'C', 'D', 'E']

// which central server the dashboard is using right now
let activeApi = PRIMARY_API

// send one request to one central server
// returns null if that central server could not be reached
async function sendTo(base, path, options) {
  let response
  try {
    response = await fetch(`${base}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    })
  } catch {
    return null
  }

  const text = await response.text()
  let data

  try {
    data = text ? JSON.parse(text) : null
  } catch {
    data = null
  }

  // the Vite proxy answers 5xx with no JSON when the central server is down
  if (response.status >= 500 && data === null) {
    return null
  }

  return { response, data: data ?? {} }
}

async function apiRequest(path, options = {}) {
  const other = activeApi === PRIMARY_API ? BACKUP_API : PRIMARY_API

  // try the current central server first, then fail over to the other one
  let result = await sendTo(activeApi, path, options)

  if (result === null) {
    result = await sendTo(other, path, options)

    if (result === null) {
      throw new Error('Both central servers are unavailable.')
    }

    activeApi = other
    console.log(`Switched to ${activeApi === PRIMARY_API ? 'primary' : 'backup'} central server`)
  }

  const { response, data } = result

  if (!response.ok) {
    throw new Error(
      data.error || data.message || `Request failed (${response.status})`
    )
  }

  return data
}

function asArray(data, key) {
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.[key])) return data[key]
  return []
}

function getSpotId(spot) {
  if (typeof spot !== 'object') return spot
  return spot.spot_id ?? spot.id ?? spot.spot_number
}

function spotIsReserved(spot) {
  const status = String(spot.status ?? '').toLowerCase()
  return (
    spot.is_reserved === true ||
    spot.reserved === true ||
    spot.is_available === false ||
    spot.available === false ||
    ['reserved', 'occupied', 'booked'].includes(status)
  )
}

export default function App() {
  const [lots, setLots] = useState([])
  const [selectedLot, setSelectedLot] = useState('A')
  const [spots, setSpots] = useState([])
  const [reservations, setReservations] = useState([])
  const [userName, setUserName] = useState('')
  const [selectedSpot, setSelectedSpot] = useState(null)
  const [loading, setLoading] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  const currentLot = lots.find(
    lot => String(lot.lot_id) === selectedLot
  )

  const loadLots = useCallback(async () => {
    const data = await apiRequest('/lots')
    setLots(asArray(data, 'lots'))
  }, [])

  const loadLotDetails = useCallback(async (lotId) => {
    const [spotsData, reservationsData] = await Promise.all([
      apiRequest(`/lots/${lotId}/spots`),
      apiRequest(`/lots/${lotId}/reservations`),
    ])

    setSpots(asArray(spotsData, 'spots'))
    setReservations(asArray(reservationsData, 'reservations'))
  }, [])

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      await loadLots()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [loadLots])

  useEffect(() => {
    refresh()
    const timer = setInterval(refresh, 5000)
    return () => clearInterval(timer)
  }, [refresh])

  useEffect(() => {
    let active = true

    async function load() {
      setError('')
      try {
        const [spotsData, reservationsData] = await Promise.all([
          apiRequest(`/lots/${selectedLot}/spots`),
          apiRequest(`/lots/${selectedLot}/reservations`),
        ])

        if (active) {
          setSpots(asArray(spotsData, 'spots'))
          setReservations(asArray(reservationsData, 'reservations'))
        }
      } catch (err) {
        if (active) {
          setSpots([])
          setReservations([])
          setError(err.message)
        }
      }
    }

    load()
    const timer = setInterval(load, 5000)

    return () => {
      active = false
      clearInterval(timer)
    }
  }, [selectedLot])

  async function reserveSpot() {
    if (!userName.trim()) {
      setError('Please enter your name.')
      return
    }

    if (selectedSpot === null) {
      setError('Please select an available parking spot.')
      return
    }

    setBusy(true)
    setError('')
    setMessage('')

    try {
      await apiRequest(`/lots/${selectedLot}/reserve`, {
        method: 'POST',
        body: JSON.stringify({
          spot_id: selectedSpot,
          user_name: userName.trim(),
        }),
      })

      setMessage(`Spot ${selectedSpot} reserved successfully!`)
      setSelectedSpot(null)
      await loadLots()
      await loadLotDetails(selectedLot)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function releaseSpot(reservationId) {
    setBusy(true)
    setError('')
    setMessage('')

    try {
      await apiRequest(`/lots/${selectedLot}/release`, {
        method: 'POST',
        body: JSON.stringify({
          reservation_id: reservationId,
        }),
      })

      setMessage('Parking reservation released successfully!')
      await loadLots()
      await loadLotDetails(selectedLot)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const totalCapacity = lots.reduce(
    (sum, lot) => sum + Number(lot.capacity || 0), 0
  )

  const availableSpaces = lots.reduce(
    (sum, lot) => sum + (
      lot.status === 'online' ? Number(lot.available || 0) : 0
    ), 0
  )

  const onlineLots = lots.filter(
    lot => lot.status === 'online'
  ).length

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <div className="brand">
            <div className="brand-icon">P</div>
            <div>
              <h1>OTU Smart Parking</h1>
              <p>Distributed Parking Management System</p>
            </div>
          </div>
          <span className="header-tag">Ontario Tech University</span>
        </div>
      </header>

      <main className="container">
        <section className="welcome">
          <div>
            <h2>Parking Dashboard</h2>
            <p>Monitor parking availability and manage reservations.</p>
          </div>
          <button className="refresh-btn" onClick={refresh} disabled={loading}>
            {loading ? 'Refreshing...' : '↻ Refresh'}
          </button>
        </section>

        {error && <div className="alert error">{error}</div>}
        {message && <div className="alert success">{message}</div>}

        <section className="stats">
          <div className="stat-card">
            <span>Total Spaces</span>
            <strong>{totalCapacity}</strong>
            <small>Across all parking lots</small>
          </div>
          <div className="stat-card">
            <span>Available Spaces</span>
            <strong className="green">{availableSpaces}</strong>
            <small>Currently available in online lots</small>
          </div>
          <div className="stat-card">
            <span>Reserved Spaces</span>
            <strong>
              {lots.reduce(
                (sum, lot) => sum + Number(lot.reserved || 0), 0
              )}
            </strong>
            <small>Active reservations</small>
          </div>
          <div className="stat-card">
            <span>Online Servers</span>
            <strong className="blue">{onlineLots}/5</strong>
            <small>Parking lot servers</small>
          </div>
        </section>

        <section className="section">
          <h3>Parking Lots</h3>
          <p className="section-subtitle">
            Select a parking lot to view spaces and reservations.
          </p>

          <div className="lot-grid">
            {LOT_IDS.map(id => {
              const lot = lots.find(
                item => String(item.lot_id) === id
              )
              const online = lot?.status === 'online'

              return (
                <button
                  key={id}
                  className={`lot-card ${selectedLot === id ? 'selected' : ''}`}
                  onClick={() => {
                    setSelectedLot(id)
                    setSelectedSpot(null)
                    setError('')
                    setMessage('')
                  }}
                >
                  <div className="lot-top">
                    <strong>Lot {id}</strong>
                    <span className={`status ${online ? 'online' : 'offline'}`}>
                      {online ? '● Online' : '● Offline'}
                    </span>
                  </div>

                  <div className="lot-availability">
                    {online ? lot.available : '—'}
                    <small> / {lot?.capacity ?? '—'} available</small>
                  </div>

                  <div className="progress">
                    <div
                      style={{
                        width: online && lot.capacity
                          ? `${(lot.available / lot.capacity) * 100}%`
                          : '0%',
                      }}
                    />
                  </div>
                </button>
              )
            })}
          </div>
        </section>

        <section className="section panel">
          <div className="panel-heading">
            <div>
              <h3>Lot {selectedLot} — Parking Spaces</h3>
              <p className="section-subtitle">
                Green spaces are available. Red spaces are reserved.
              </p>
            </div>
            <span className={`status ${currentLot?.status === 'online' ? 'online' : 'offline'}`}>
              {currentLot?.status === 'online' ? '● Online' : '● Offline'}
            </span>
          </div>

          {currentLot?.status !== 'online' ? (
            <div className="empty-state">
              This parking lot is currently offline.
            </div>
          ) : spots.length === 0 ? (
            <div className="empty-state">
              No parking spot information available.
            </div>
          ) : (
            <div className="spot-grid">
              {spots.map(spot => {
                const id = getSpotId(spot)
                const reserved = spotIsReserved(spot)

                return (
                  <button
                    key={id}
                    disabled={reserved || busy}
                    onClick={() => setSelectedSpot(id)}
                    className={`spot ${reserved ? 'reserved' : 'available'} ${
                      selectedSpot === id ? 'chosen' : ''
                    }`}
                    title={`Spot ${id}: ${reserved ? 'Reserved' : 'Available'}`}
                  >
                    <span>🚗</span>
                    <strong>{id}</strong>
                  </button>
                )
              })}
            </div>
          )}

          <div className="legend">
            <span><i className="legend-green" /> Available</span>
            <span><i className="legend-red" /> Reserved</span>
            <span><i className="legend-blue" /> Selected</span>
          </div>
        </section>

        <div className="bottom-grid">
          <section className="section panel">
            <h3>Reserve a Parking Space</h3>
            <p className="section-subtitle">
              Choose an available spot and enter your name.
            </p>

            <label htmlFor="user-name">Your Name</label>
            <input
              id="user-name"
              type="text"
              placeholder="Enter your full name"
              value={userName}
              onChange={e => setUserName(e.target.value)}
            />

            <label>Selected Parking Lot</label>
            <div className="selection-value">Lot {selectedLot}</div>

            <label>Selected Parking Spot</label>
            <div className="selection-value">
              {selectedSpot === null
                ? 'No spot selected'
                : `Spot ${selectedSpot}`}
            </div>

            <button
              className="primary-btn"
              onClick={reserveSpot}
              disabled={
                busy ||
                selectedSpot === null ||
                currentLot?.status !== 'online'
              }
            >
              {busy ? 'Processing...' : 'Reserve Parking Spot'}
            </button>
          </section>

          <section className="section panel">
            <h3>Active Reservations</h3>
            <p className="section-subtitle">
              Current reservations for Lot {selectedLot}.
            </p>

            {reservations.length === 0 ? (
              <div className="empty-state">
                No active reservations for this lot.
              </div>
            ) : (
              <div className="reservation-list">
                {reservations.map((reservation, index) => {
                  const reservationId =
                    reservation.reservation_id ?? reservation.id

                  return (
                    <div
                      className="reservation"
                      key={reservationId ?? index}
                    >
                      <div>
                        <strong>
                          Spot {reservation.spot_id ?? reservation.spot_number}
                        </strong>
                        <p>{reservation.user_name ?? 'User'}</p>
                      </div>
                      <button
                        className="release-btn"
                        disabled={busy || reservationId == null}
                        onClick={() => releaseSpot(reservationId)}
                      >
                        Release
                      </button>
                    </div>
                  )
                })}
              </div>
            )}
          </section>
        </div>
      </main>

      <footer className="footer">
        SOFE 4790U — Distributed Systems | Ontario Tech University
      </footer>
    </div>
  )
}
