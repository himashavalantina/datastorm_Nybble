import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import './App.css';

function App() {
  const [outletId, setOutletId] = useState('OUT_00001');
  const [outletData, setOutletData] = useState(null);
  const [explanation, setExplanation] = useState('');
  const [displayedText, setDisplayedText] = useState(''); // For typewriter effect
  const [loadingMetrics, setLoadingMetrics] = useState(false);
  const [loadingAi, setLoadingAi] = useState(false);
  const [error, setError] = useState(null);

  // Typewriter effect logic
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
      }, 20); // Speed of typing
      return () => clearInterval(timer);
    }
  }, [explanation]);

  const fetchMetrics = async () => {
    setLoadingMetrics(true);
    setError(null);
    setExplanation('');
    setDisplayedText('');
    
    try {
      const response = await fetch(`http://localhost:8000/api/outlets/${outletId}`);
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
      const response = await fetch(`http://localhost:8000/api/explain/${outletId}`, {
        method: 'POST'
      });
      const data = await response.json();
      setExplanation(data.explanation);
    } catch (err) {
      setExplanation('Failed to connect to AI Core.');
    } finally {
      setLoadingAi(false);
    }
  };

  // Calculations for Badges and Charts
  const volumeLift = outletData 
    ? (((outletData.Predicted_Maximum_Liters - outletData.Base_Historical_Max) / outletData.Base_Historical_Max) * 100).toFixed(1)
    : 0;

  const getSaturationBadge = (index) => {
    if (index > 0.7) return { text: 'HIGH SATURATION', class: 'badge-high' };
    if (index > 0.4) return { text: 'MEDIUM SATURATION', class: 'badge-mid' };
    return { text: 'LOW SATURATION', class: 'badge-low' };
  };

  const chartData = outletData ? [
    { name: 'Historical Max', Volume: outletData.Base_Historical_Max },
    { name: 'Predicted Potential', Volume: outletData.Predicted_Maximum_Liters }
  ] : [];

  return (
    <div className="app-wrapper">
      <div className="dashboard-container">
        
        {/* NEW: Branded Header */}
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

        <main className="dashboard-content">
          <section className="search-section">
            <h2>OUTLET TARGETING</h2>
            <div className="search-bar">
              <input 
                type="text" 
                value={outletId} 
                onChange={(e) => setOutletId(e.target.value)}
                placeholder="Enter Outlet ID..."
              />
              <button onClick={fetchMetrics} disabled={loadingMetrics}>
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
                      <Tooltip cursor={{fill: '#ffffff10'}} contentStyle={{ backgroundColor: '#000', border: '1px solid #3FFF00' }}/>
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
                <p className="xai-description">
                  Deploy XAI engine to translate spatial and historical feature weights into business intelligence.
                </p>
                <button className="ai-btn" onClick={generateInsights} disabled={loadingAi}>
                  {loadingAi ? 'NEURAL NET PROCESSING...' : '⚡ GENERATE INSIGHTS'}
                </button>
                
                {explanation && (
                  <div className="explanation-box">
                    <div className="ai-header">
                      <span className="blink-cursor">_</span> SYSTEM RESPONSE
                    </div>
                    <p className="typewriter-text">{displayedText}</p>
                  </div>
                )}
              </section>
            </div>
          )}
        </main>
      </div>

      {/* NEW: Branded Footer */}
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