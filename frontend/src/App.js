import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import './App.css';

function App() {
  const [activeView, setActiveView] = useState('analyze'); // 'analyze' or 'browse'
  const [outletId, setOutletId] = useState('OUT_00001');
  const [outletData, setOutletData] = useState(null);
  const [explanation, setExplanation] = useState('');
  const [displayedText, setDisplayedText] = useState(''); 
  const [loadingMetrics, setLoadingMetrics] = useState(false);
  const [loadingAi, setLoadingAi] = useState(false);
  const [error, setError] = useState(null);

  // Directory State
  const [allOutlets, setAllOutlets] = useState([]);
  const [filterProv, setFilterProv] = useState('All');
  const [filterDist, setFilterDist] = useState('All');

  // Fetch Directory Data on Load
  useEffect(() => {
    fetch(`http://localhost:8000/api/outlets`)
      .then(res => res.json())
      .then(data => setAllOutlets(data.outlets || []))
      .catch(err => console.error("Failed to load directory", err));
  }, []);

  useEffect(() => {
    if (explanation) {
      let i = 0;
      setDisplayedText('');
      const timer = setInterval(() => {
        if (i < explanation.length) {
          setDisplayedText((prev) => prev + explanation.charAt(i));
          i++;
        } else {
          clearInterval(timer);
        }
      }, 20);
      return () => clearInterval(timer);
    }
  }, [explanation]);

  const fetchMetrics = async (targetId = outletId) => {
    setOutletId(targetId);
    setActiveView('analyze');
    setLoadingMetrics(true);
    setError(null);
    setExplanation('');
    setDisplayedText('');
    
    try {
      const response = await fetch(`http://localhost:8000/api/outlets/${targetId}`);
      if (!response.ok) throw new Error('Outlet not found');
      const data = await response.json();
      setOutletData(data);
    } catch (err) {
      setError(err.message);
      setOutletData(null);
    } finally {
      setLoadingMetrics(false);
    }
  };

  const generateInsights = async () => {
    setLoadingAi(true);
    try {
      const response = await fetch(`http://localhost:8000/api/explain/${outletId}`, { method: 'POST' });
      const data = await response.json();
      setExplanation(data.explanation);
    } catch (err) {
      setExplanation('Failed to connect to AI Core.');
    } finally {
      setLoadingAi(false);
    }
  };

  const volumeLift = outletData ? (((outletData.Predicted_Maximum_Liters - outletData.Base_Historical_Max) / outletData.Base_Historical_Max) * 100).toFixed(1) : 0;
  
  const getSaturationBadge = (index) => {
    if (index > 0.7) return { text: 'HIGH SATURATION', class: 'badge-high' };
    if (index > 0.4) return { text: 'MEDIUM SATURATION', class: 'badge-mid' };
    return { text: 'LOW SATURATION', class: 'badge-low' };
  };

  const chartData = outletData ? [
    { name: 'Historical Max', Volume: outletData.Base_Historical_Max },
    { name: 'Predicted Potential', Volume: outletData.Predicted_Maximum_Liters }
  ] : [];

  // Filter Logic
  const filteredOutlets = allOutlets.filter(o => {
    const matchProv = filterProv === 'All' || o.Province === filterProv;
    const matchDist = filterDist === 'All' || o.Distributor === filterDist;
    return matchProv && matchDist;
  });

  const uniqueProvinces = ['All', ...new Set(allOutlets.map(o => o.Province))];
  const uniqueDistributors = ['All', ...new Set(allOutlets.map(o => o.Distributor))];

  return (
    <div className="app-wrapper">
      <div className="dashboard-container">
        
        <header className="dashboard-header">
          <div className="header-top">
            <div className="logo-group">
              <div className="pulse-dot"></div>
              <div className="title-stack">
                <h1>DATA STORM <span className="version">V 7.0</span></h1>
                <span className="subtitle">Critical Analysis Inspired Solutions</span>
              </div>
            </div>
            <div className="team-badge">
              <span className="team-label">Developed By</span>
              <span className="team-name">Team Nybble</span>
            </div>
          </div>
        </header>

        {/* View Navigation Tabs */}
        <div className="nav-tabs">
          <button className={activeView === 'browse' ? 'tab active-tab' : 'tab'} onClick={() => setActiveView('browse')}>
            📂 Dataset Directory
          </button>
          <button className={activeView === 'analyze' ? 'tab active-tab' : 'tab'} onClick={() => setActiveView('analyze')}>
            🎯 Outlet Targeting
          </button>
        </div>

        <main className="dashboard-content">
          
          {/* DIRECTORY VIEW */}
          {activeView === 'browse' && (
            <section className="directory-section slide-up">
              <div className="filter-bar">
                <div className="filter-group">
                  <label>Filter by Province</label>
                  <select value={filterProv} onChange={e => setFilterProv(e.target.value)}>
                    {uniqueProvinces.map(p => <option key={p} value={p}>{p}</option>)}
                  </select>
                </div>
                <div className="filter-group">
                  <label>Filter by Distributor</label>
                  <select value={filterDist} onChange={e => setFilterDist(e.target.value)}>
                    {uniqueDistributors.map(d => <option key={d} value={d}>{d}</option>)}
                  </select>
                </div>
                <div className="result-count">Showing {filteredOutlets.length} Outlets</div>
              </div>

              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Outlet ID</th>
                      <th>Province</th>
                      <th>Distributor</th>
                      <th>Predicted Volume (L)</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredOutlets.map(outlet => (
                      <tr key={outlet.Outlet_ID}>
                        <td className="highlight-cell">{outlet.Outlet_ID}</td>
                        <td>{outlet.Province}</td>
                        <td>{outlet.Distributor}</td>
                        <td className="volume-cell">{parseFloat(outlet.Predicted_Maximum_Liters || outlet.Maximum_Monthly_Liters || 0).toFixed(1)} L</td>
                        <td>
                          <button className="analyze-sm-btn" onClick={() => fetchMetrics(outlet.Outlet_ID)}>Analyze →</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {/* ANALYZE VIEW */}
          {activeView === 'analyze' && (
            <div className="slide-up">
              <section className="search-section">
                <h2>TARGETED SCAN</h2>
                <div className="search-bar">
                  <input type="text" value={outletId} onChange={(e) => setOutletId(e.target.value)} placeholder="Enter Outlet ID..." />
                  <button onClick={() => fetchMetrics(outletId)} disabled={loadingMetrics}>
                    {loadingMetrics ? 'SCANNING...' : 'INITIATE SCAN'}
                  </button>
                </div>
                {error && <p className="error-text">{error}</p>}
              </section>

              {loadingMetrics && (
                <div className="results-grid">
                  <div className="skeleton-card pulse"></div>
                  <div className="skeleton-card pulse"></div>
                </div>
              )}

              {outletData && !loadingMetrics && (
                <div className="results-grid slide-up">
                  <section className="metrics-card">
                    <div className="card-header">
                      <h3>VOLUME POTENTIAL</h3>
                      <span className="roi-badge">📈 +{volumeLift}% LIFT</span>
                    </div>
                    
                    <div className="metric-row">
                      <span className="metric-label">Historical Ceiling:</span>
                      <span className="metric-value">{outletData.Base_Historical_Max} L</span>
                    </div>
                    <div className="metric-row highlight">
                      <span className="metric-label">Latent Potential:</span>
                      <span className="metric-value">{outletData.Predicted_Maximum_Liters} L</span>
                    </div>

                    <div className="chart-container">
                      <ResponsiveContainer width="100%" height={150}>
                        <BarChart data={chartData}>
                          <Tooltip cursor={{fill: '#ffffff10'}} contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #0BDA51' }}/>
                          <XAxis dataKey="name" stroke="#ffffff" fontSize={12} tickLine={false} axisLine={false}/>
                          <Bar dataKey="Volume" radius={[4, 4, 0, 0]}>
                            {chartData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={index === 0 ? '#00BFFF' : '#29E373'} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>

                    <hr className="divider" />
                    
                    <h3>CATCHMENT FACTORS</h3>
                    <div className="metric-row">
                      <span className="metric-label">Nearby Education Hubs:</span>
                      <span className="metric-value">{outletData.Schools_Nearby}</span>
                    </div>
                    <div className="metric-row">
                      <span className="metric-label">Market Saturation:</span>
                      <span className={`saturation-badge ${getSaturationBadge(outletData.Market_Saturation_Index).class}`}>
                        {getSaturationBadge(outletData.Market_Saturation_Index).text}
                      </span>
                    </div>
                  </section>

                  <section className="xai-card">
                    <h3>AI STRATEGIC ADVISOR</h3>
                    <p className="xai-description">Deploy XAI engine to translate feature weights into business intelligence.</p>
                    <button className="ai-btn" onClick={generateInsights} disabled={loadingAi}>
                      {loadingAi ? 'NEURAL NET PROCESSING...' : '⚡ GENERATE INSIGHTS'}
                    </button>
                    
                    {explanation && (
                      <div className="explanation-box">
                        <div className="ai-header"><span className="blink-cursor">_</span> SYSTEM RESPONSE</div>
                        <p className="typewriter-text">{displayedText}</p>
                      </div>
                    )}
                  </section>
                </div>
              )}
            </div>
          )}
        </main>
      </div>

      <footer className="dashboard-footer">
        <div className="footer-content">
          <div className="footer-left">
            <span className="footer-label">Organized By</span>
            <span className="footer-text">Rotaract Club of University of Moratuwa</span>
          </div>
          <div className="footer-right">
            <span className="footer-label">Powered By</span>
            <span className="footer-text octave">OCTAVE</span>
            <span className="footer-subtext">John Keells Group</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;