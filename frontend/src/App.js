import React, { useState, useEffect, useRef, useCallback } from 'react';
import * as api from './api';
import './App.css';

// --- Main App Component ---
function App() {
  const [currentView, setCurrentView] = useState('intro-ai');
  
  // Form & Data States
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [firebaseUid, setFirebaseUid] = useState('');
  const [cardNickname, setCardNickname] = useState('');
  const [bankName, setBankName] = useState('');
  const [lastFourDigits, setLastFourDigits] = useState('');
  const [offerDescription, setOfferDescription] = useState('');
  const [offerExpiryDate, setOfferExpiryDate] = useState('');
  const [user, setUser] = useState(null);
  const [selectedCardId, setSelectedCardId] = useState(null);
  const [searchTerm, setSearchTerm] = useState(''); // NEW STATE for search

  // OCR States
  const [isScanning, setIsScanning] = useState(false);
  const [scannedOffers, setScannedOffers] = useState([]);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const fileInputRef = useRef(null);

  // Smart Spend States
  const [smartSpendQuery, setSmartSpendQuery] = useState('');
  const [smartSpendResult, setSmartSpendResult] = useState(null);
  const [isSmartSpendOpen, setIsSmartSpendOpen] = useState(false);
  
  // Alerts State
  const [isAlertsOpen, setIsAlertsOpen] = useState(false);
  const [priorityAlerts, setPriorityAlerts] = useState([]);

  // Preferences & Digest States
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [digestDay, setDigestDay] = useState('Sunday');
  const [weeklyDigest, setWeeklyDigest] = useState(null);

  // UI States
  const [message, setMessage] = useState({ text: '', type: '' });
  const [isLoading, setIsLoading] = useState(false);
  const isThrottled = useRef(false);

  const changeView = useCallback((newView) => { 
    if (newView === 'card') {
      setCardNickname('');
      setBankName('');
      setLastFourDigits('');
    }
    // Reset search term when leaving the offers view
    if (currentView === 'view-offers' && newView !== 'view-offers') {
      setSearchTerm('');
    }
    setCurrentView(newView); 
  }, [currentView]);
  
  useEffect(() => {
    document.body.className = `view-${currentView}`;
  }, [currentView]);

  useEffect(() => {
    const handleNavigation = (event) => {
      if (currentView.startsWith('intro-') && !isThrottled.current) {
        isThrottled.current = true;
        setTimeout(() => { isThrottled.current = false; }, 1200);
        const isScrollingDown = (event.deltaY && event.deltaY > 0) || event.key === 'ArrowDown';
        if (isScrollingDown) {
          if (currentView === 'intro-ai') changeView('intro-title');
          else if (currentView === 'intro-title') changeView('login');
        }
      }
    };
    window.addEventListener('wheel', handleNavigation);
    window.addEventListener('keydown', handleNavigation);
    return () => {
      window.removeEventListener('wheel', handleNavigation);
      window.removeEventListener('keydown', handleNavigation);
    };
  }, [currentView, changeView]);

  const handleSetMessage = (error, type, duration = 4000) => {
    let text = 'An unknown error occurred.';
    const detail = error.response?.data?.detail || error.message;

    if (detail) {
        if (Array.isArray(detail) && detail.length > 0 && detail[0].msg) {
            text = `Error: ${detail[0].msg}`;
        } else if (typeof detail === 'string') {
            text = detail;
        } else {
            text = JSON.stringify(detail);
        }
    }
    
    setMessage({ text, type });
    setTimeout(() => setMessage({ text: '', type: '' }), duration);
  };
  
  const showSuccessMessage = (text, duration = 4000) => {
    setMessage({ text, type: 'success' });
    setTimeout(() => setMessage({ text: '', type: '' }), duration);
  };
  
  const loadDashboard = useCallback(async (userId) => {
    setIsLoading(true);
    try {
        const currentUser = await api.getUserById(userId);
        setUser(currentUser);
        if (currentUser.preferences) {
          setDigestDay(currentUser.preferences.digest_day);
        }

        const alertsData = await api.getAlerts(userId);
        setPriorityAlerts(alertsData);
        changeView('dashboard');
    } catch (error) {
        handleSetMessage(error, 'error');
        changeView('login');
    } finally {
      setIsLoading(false);
    }
  }, [changeView]);

  const handleLogin = async () => {
    setIsLoading(true);
    try {
      const existingUser = await api.getUserByFirebaseId(firebaseUid);
      showSuccessMessage(`Welcome back, ${existingUser.username}!`);
      
      if (existingUser && existingUser.user_id) {
        loadDashboard(existingUser.user_id);
      } else {
        handleSetMessage({ message: 'Login succeeded, but could not fetch user details.' }, 'error');
      }
      
    } catch (error) {
      handleSetMessage(error, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateUser = async () => {
    setIsLoading(true);
    try {
      const newUser = await api.createUser({ email, username, firebase_uid: firebaseUid });
      setUser(newUser);
      showSuccessMessage(`Welcome, ${newUser.username}! Account created.`);
      changeView('card');
    } catch (error) {
      handleSetMessage(error, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddCard = async () => {
    setIsLoading(true);
    try {
      await api.addCard({ card_nickname: cardNickname, bank_name: bankName, last_four_digits: lastFourDigits, user_id: user.user_id });
      showSuccessMessage(`Card "${cardNickname}" added!`);
      loadDashboard(user.user_id);
    } catch (error) {
      handleSetMessage(error, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddOffer = async (offerData) => {
    // This function is now primarily used by handleSaveAllScannedOffers
    // Manual additions will use a different path or could be adapted later
    await api.addOffer(offerData);
  };

  const handleSaveAllScannedOffers = useCallback(async () => {
    setIsLoading(true);
    showSuccessMessage(`Saving ${scannedOffers.length} scanned offers...`);

    const offerPromises = scannedOffers.map(offer => 
      api.addOffer({ 
        description: offer.description, 
        expiry_date: offer.expiry_date, 
        card_id: selectedCardId,
        category: offer.category // Pass category to API
      })
    );

    const results = await Promise.allSettled(offerPromises);

    const successfulSaves = results.filter(res => res.status === 'fulfilled').length;
    const failedSaves = results.length - successfulSaves;

    if (failedSaves > 0) {
      const firstErrorResult = results.find(res => res.status === 'rejected');
      const errorMessage = firstErrorResult.reason.response?.data?.detail || 'One or more offers had an invalid format.';
      handleSetMessage({ response: { data: { detail: `${successfulSaves} offers saved, ${failedSaves} failed. Reason: ${JSON.stringify(errorMessage)}` } } }, 'error', 8000);
    } else {
      showSuccessMessage("All offers saved successfully!");
    }
    
    if (user && user.user_id) {
      loadDashboard(user.user_id);
    }
    
    setIsLoading(false);
  }, [scannedOffers, selectedCardId, user, loadDashboard]);
  
  const handleUpdateOfferStatus = useCallback(async (offerId, newStatus) => {
    let amountSaved = null;
    if (newStatus === 'used') {
        const savedInput = window.prompt("How much did you save with this offer?");
        if (savedInput === null) return;

        const savedFloat = parseFloat(savedInput);
        if (isNaN(savedFloat) || savedFloat < 0) {
            handleSetMessage({ message: "Please enter a valid number for the amount saved." }, 'error');
            return;
        }
        amountSaved = savedFloat;
    }

    try {
        await api.updateOfferStatus(offerId, newStatus, amountSaved);
        showSuccessMessage(`Offer marked as ${newStatus}.`);
        loadDashboard(user.user_id); // Reload to reflect changes
    } catch (error) {
        handleSetMessage(error, 'error');
    }
  }, [user, loadDashboard]);

  const handleFileChange = (event) => {
    if (event.target.files) {
      setSelectedFiles(Array.from(event.target.files));
    }
  };

  const handleScanOffers = async () => {
    if (selectedFiles.length === 0 || !selectedCardId) return;
    setIsScanning(true);
    try {
      const result = await api.scanOffers(selectedFiles);
      setScannedOffers(result.offers);
      showSuccessMessage(`Scan complete! ${result.offers.length} offers found.`);
      changeView('scan-results');
    } catch (error) {
      handleSetMessage(error, "error");
    } finally {
      setIsScanning(false);
      setSelectedFiles([]);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleSmartSpend = async () => {
    if (!smartSpendQuery) return;
    setIsLoading(true);
    setSmartSpendResult(null);
    try {
      const result = await api.analyzeSpend({ user_id: user.user_id, query: smartSpendQuery });
      setSmartSpendResult(result);
    } catch (error) {
      handleSetMessage(error, "error");
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdatePreferences = async () => {
    setIsLoading(true);
    try {
      await api.updatePreferences(user.user_id, { digest_day: digestDay });
      showSuccessMessage('Preferences saved successfully!');
      loadDashboard(user.user_id);
    } catch (error) {
      handleSetMessage(error, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateDigest = async () => {
    setIsLoading(true);
    setWeeklyDigest(null);
    try {
      const result = await api.generateDigest(user.user_id);
      setWeeklyDigest(result);
      showSuccessMessage('Your Weekly Digest is ready!');
    } catch (error) {
      handleSetMessage(error, "error");
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => { 
    setUser(null); 
    setUsername(''); 
    setEmail(''); 
    setFirebaseUid(''); 
    setIsSettingsOpen(false);
    setIsSmartSpendOpen(false);
    setIsAlertsOpen(false);
    setCurrentView('intro-ai');
  };

  const promptOfferChoice = (cardId) => { setSelectedCardId(cardId); changeView('add-offer-choice'); };
  const viewCardOffers = (cardId) => { setSelectedCardId(cardId); changeView('view-offers'); };
  const getSelectedCard = () => { if (!user || !selectedCardId) return null; return user.cards.find(c => c.card_id === selectedCardId); };
  const selectedCardObject = getSelectedCard();

  const calculateTotalSavings = () => {
    if (!user || !user.cards) return 0;
    
    let total = 0;
    user.cards.forEach(card => {
        card.offers.forEach(offer => {
            if (offer.status === 'used' && offer.amount_saved) {
                total += parseFloat(offer.amount_saved);
            }
        });
    });
    return total.toFixed(2);
  };
  
  const totalSavings = user ? calculateTotalSavings() : 0;

  // --- NEW: Helper function to filter and group offers ---
  const getCategorizedAndFilteredOffers = () => {
      if (!selectedCardObject || !selectedCardObject.offers) return {};
      
      const filtered = selectedCardObject.offers.filter(offer => 
          offer.status === 'available' && 
          offer.description.toLowerCase().includes(searchTerm.toLowerCase())
      );
      
      const grouped = filtered.reduce((acc, offer) => {
          const category = offer.category || 'General';
          if (!acc[category]) {
              acc[category] = [];
          }
          acc[category].push(offer);
          return acc;
      }, {});

      return grouped;
  };

  const categorizedOffers = getCategorizedAndFilteredOffers();

  return (
    <div className="App">
      <section className={`scroll-section ${currentView === 'intro-ai' ? 'visible' : ''}`}><h1 className="intro-ai-text">AI</h1></section>
      <section className={`scroll-section ${currentView === 'intro-title' ? 'visible' : ''}`}><h1 className="intro-title-text">SmartWallet</h1></section>
      
      {currentView === 'view-offers' && (
        <>
          <button 
            onClick={() => changeView('dashboard')} 
            className="nav-button tertiary"
            style={{ position: 'absolute', top: '2rem', right: '2rem', zIndex: 100 }}
          >
            Back to Dashboard
          </button>
          
          <div className="global-offers-header" style={{ position: 'absolute', top: '2rem', left: '50%', transform: 'translateX(-50%)', zIndex: 100, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <h2>Offers for {selectedCardObject?.card_nickname}</h2>
            <div className="search-bar-container">
                <input 
                    type="text"
                    placeholder="Search offers..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="offer-search-input"
                />
            </div>
          </div>
        </>
      )}

      <main className={`main-content ${!currentView.startsWith('intro-') ? 'visible' : ''}`} style={currentView === 'view-offers' ? { paddingTop: '150px' } : {}}>
        {currentView === 'login' && (
          <div className="step-content">
            <h2>Sign In or Create Account</h2>
            <form className="user-form" onSubmit={(e) => e.preventDefault()}>
              <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Username (for new account)" />
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email (for new account)" />
              <input type="text" value={firebaseUid} onChange={(e) => setFirebaseUid(e.target.value)} placeholder="PIN / Unique ID" required />
            </form>
            <div className="navigation-buttons">
              <button onClick={handleLogin} disabled={isLoading || !firebaseUid} className="nav-button secondary">{isLoading ? "..." : "Login with PIN"}</button>
              <button onClick={handleCreateUser} disabled={isLoading || !email || !username || !firebaseUid} className="nav-button primary">{isLoading ? "..." : "Create Account"}</button>
            </div>
          </div>
        )}

        {currentView === 'card' && (
          <div className="step-content">
            <h2>{user && user.cards && user.cards.length > 0 ? "Add Another Card" : "Add Your First Card"}</h2>
            <form className="user-form" onSubmit={(e) => e.preventDefault()}>
              <input type="text" value={cardNickname} onChange={(e) => setCardNickname(e.target.value)} placeholder="Card Nickname (e.g., BofA Rewards)" required />
              <input type="text" value={bankName} onChange={(e) => setBankName(e.target.value)} placeholder="Bank Name" required />
              <input type="text" value={lastFourDigits} onChange={(e) => setLastFourDigits(e.target.value)} placeholder="Last Four Digits" maxLength="4" required />
            </form>
            <div className="navigation-buttons">
              <button onClick={() => changeView(user && user.cards && user.cards.length > 0 ? 'dashboard' : 'login')} className="nav-button secondary">Back</button>
              <button 
                onClick={handleAddCard} 
                disabled={isLoading || !cardNickname.trim() || !bankName.trim() || !lastFourDigits.trim()} 
                className="nav-button primary"
              >
                {isLoading ? "Saving..." : "Save Card"}
              </button>
            </div>
          </div>
        )}

        {currentView === 'add-offer-choice' && (
          <div className="step-content">
            <h2>Add Offer to Card: {selectedCardObject?.card_nickname}</h2>
            <p>How would you like to add your new offer?</p>
            <div className="dashboard-actions">
              <button onClick={() => changeView('offer')} className="nav-button primary">Add Manually</button>
              <button onClick={() => changeView('scan')} className="nav-button secondary">Scan from Image</button>
            </div>
            <div className="navigation-buttons">
              <button onClick={() => changeView('dashboard')} className="nav-button tertiary">Back to Dashboard</button>
            </div>
          </div>
        )}

        {currentView === 'offer' && (
           <div className="step-content">
            <h2>Add Offer to Card: {selectedCardObject?.card_nickname}</h2>
            <form className="user-form" onSubmit={(e) => e.preventDefault()}>
              <input type="text" value={offerDescription} onChange={(e) => setOfferDescription(e.target.value)} placeholder="Offer Description" required />
              <input type="date" value={offerExpiryDate} onChange={(e) => setOfferExpiryDate(e.target.value)} required />
            </form>
            <div className="navigation-buttons">
              <button onClick={() => changeView('add-offer-choice')} className="nav-button secondary">Back</button>
              <button onClick={() => handleAddOffer({description: offerDescription, expiry_date: offerExpiryDate, card_id: selectedCardId, category: 'General'})} disabled={isLoading} className="nav-button primary">{isLoading ? "Saving..." : "Save Offer"}</button>
            </div>
          </div>
        )}

        {currentView === 'dashboard' && (
          <>
            <div className="dashboard-content">
              <h2>{user?.username}'s Wallet</h2>
              {user ? (
                <div className="user-data">
                  <div className="savings-tracker">
                    <p>Total Savings This Year</p>
                    <h3>${totalSavings}</h3>
                  </div>

                  {user.cards && user.cards.map(cardItem => (
                    <div key={cardItem.card_id} className="card-info">
                      <div className="card-header">
                        <h4>{cardItem.card_nickname} ({cardItem.bank_name} **** {cardItem.last_four_digits})</h4>
                        <button onClick={() => promptOfferChoice(cardItem.card_id)} className="add-offer-btn" title="Add Offer">+</button>
                      </div>
                      <div className="offer-summary">
                        <p>Total Available Offers: <strong>{cardItem.offers.filter(o => o.status === 'available').length}</strong></p>
                        <button onClick={() => viewCardOffers(cardItem.card_id)} className="nav-button secondary small">View Offers</button>
                      </div>
                    </div>
                  ))}
                  <div className="dashboard-actions">
                    <button onClick={() => changeView('card')} className="nav-button primary">Add Another Card</button>
                  </div>
                </div>
              ) : <p className="loading-text">Loading dashboard...</p>}
            </div>

            <button onClick={() => setIsSettingsOpen(true)} className="fab-settings" title="Settings & Digest">⚙️</button>

            {priorityAlerts.length > 0 && (
              <button onClick={() => setIsAlertsOpen(true)} className="fab-alerts" title="Priority Alerts">
                {priorityAlerts.length}
              </button>
            )}

            <button onClick={() => setIsSmartSpendOpen(true)} className="fab-smart-spend" title="Smart Spend AI">AI</button>
          </>
        )}
        
        {currentView === 'view-offers' && (
            <div className="dashboard-content" style={{ display: 'flex', flexDirection: 'column', height: '100%', maxWidth: '800px', margin: '0 auto' }}>
                {Object.keys(categorizedOffers).length > 0 ? (
                    <div className="offers-grid-container" style={{ flex: 1, overflowY: 'auto' }}>
                        {Object.entries(categorizedOffers).map(([category, offers]) => (
                            <div key={category} className="offer-category-column">
                                <h3>{category}</h3>
                                {offers.map(offer => (
                                    <div key={offer.offer_id} className="offer-item">
                                        <div className="offer-description">
                                            {offer.description}
                                            <span>Expires: {new Date(offer.expiry_date).toLocaleDateString()}</span>
                                        </div>
                                        <div className="offer-actions">
                                            <button 
                                                onClick={() => handleUpdateOfferStatus(offer.offer_id, 'used')} 
                                                className="offer-action-btn used"
                                                style={{ minWidth: '100px' }}
                                            >
                                                Mark Used
                                            </button>
                                            <button 
                                                onClick={() => handleUpdateOfferStatus(offer.offer_id, 'dismissed')} 
                                                className="offer-action-btn dismiss"
                                                style={{ minWidth: '100px' }}
                                            >
                                                Dismiss
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ))}
                    </div>
                ) : (<p className="no-offers-text">No available offers match your search.</p>)}
            </div>
        )}

        {currentView === 'scan' && (
           <div className="step-content">
              <h2>Scan Offers for {selectedCardObject?.card_nickname}</h2>
              <p>Upload one or more screenshots of your offers.</p>
              <input 
                type="file" 
                accept="image/*" 
                onChange={handleFileChange} 
                ref={fileInputRef} 
                className="file-input"
                multiple 
              />
              {selectedFiles.length > 0 && <p className="file-selected-text">{selectedFiles.length} file(s) selected.</p>}
              <div className="navigation-buttons">
                  <button onClick={() => changeView('add-offer-choice')} className="nav-button secondary">Back</button>
                  <button 
                    onClick={handleScanOffers} 
                    disabled={isScanning || selectedFiles.length === 0 || !selectedCardId} 
                    className="nav-button primary"
                  >
                    {isScanning ? "Scanning..." : `Scan ${selectedFiles.length} Image(s)`}
                  </button>
              </div>
           </div>
        )}

        {currentView === 'scan-results' && (
            <div className="dashboard-content">
                <h2>Review Scanned Offers</h2>
                <p>Save these offers to {selectedCardObject?.card_nickname}.</p>
                <div className="scanned-offers-list">
                    {scannedOffers.map((offer, index) => (
                      <div key={index} className="scanned-offer-item">
                        <span>{offer.description}</span>
                        <span className="category-tag">{offer.category}</span>
                      </div>
                    ))}
                </div>
                 <div className="navigation-buttons">
                    <button onClick={() => changeView('scan')} className="nav-button secondary">Scan Another</button>
                    <button onClick={handleSaveAllScannedOffers} disabled={isLoading} className="nav-button primary">{isLoading ? "Saving..." : "Save All Offers"}</button>
                </div>
            </div>
        )} 
        
        {currentView === 'dashboard' && !isSmartSpendOpen && !isAlertsOpen && !isSettingsOpen && (
          <button onClick={handleLogout} className="logout-btn">Logout</button>
        )}
      </main>

      <div className={`smart-spend-overlay ${isSmartSpendOpen ? 'visible' : ''}`} onClick={() => setIsSmartSpendOpen(false)}>
        <div className={`smart-spend-panel ${isSmartSpendOpen ? 'visible' : ''}`} onClick={(e) => e.stopPropagation()}>
          <button onClick={() => setIsSmartSpendOpen(false)} className="close-panel-btn">&times;</button>
          <h2>Smart Spend AI Co-Pilot</h2>
          <p>Describe your purchase, and I'll recommend the best card to use.</p>
          <form className="user-form" onSubmit={(e) => { e.preventDefault(); handleSmartSpend(); }}>
              <input type="text" value={smartSpendQuery} onChange={(e) => setSmartSpendQuery(e.target.value)} placeholder="e.g., $150 groceries at Ralphs" required />
          </form>
          {isLoading && <p className="loading-text">Analyzing...</p>}
          {smartSpendResult && (
              <div className="smart-spend-result">
                  <h3>Recommended Card:</h3>
                  <p className="recommendation">{smartSpendResult.recommendation}</p>
                  <h3>Reason:</h3>
                  <p className="explanation">{smartSpendResult.explanation}</p>
              </div>
          )}
           <div className="navigation-buttons">
              <button onClick={handleSmartSpend} disabled={isLoading || !smartSpendQuery} className="nav-button primary">{isLoading ? "Analyzing..." : "Get Recommendation"}</button>
          </div>
        </div>
      </div>
      
      <div className={`alerts-overlay ${isAlertsOpen ? 'visible' : ''}`} onClick={() => setIsAlertsOpen(false)}>
        <div className={`alerts-panel ${isAlertsOpen ? 'visible' : ''}`} onClick={(e) => e.stopPropagation()}>
          <button onClick={() => setIsAlertsOpen(false)} className="close-panel-btn">&times;</button>
          <h2>Expiring Soon!</h2>
          <div className="alerts-list-container">
            {priorityAlerts.length > 0 ? (
              <ul>
                {priorityAlerts.map(alert => (
                  <li key={alert.offer_id}>
                    <strong>{alert.description}</strong> on your {alert.card.card_nickname}
                    <span>Expires: {new Date(alert.expiry_date).toLocaleDateString()}</span>
                  </li>
                ))}
              </ul>
            ) : <p>No offers are expiring within the next 7 days.</p>}
          </div>
        </div>
      </div>

      <div className={`settings-overlay ${isSettingsOpen ? 'visible' : ''}`} onClick={() => setIsSettingsOpen(false)}>
        <div className={`settings-panel ${isSettingsOpen ? 'visible' : ''}`} onClick={(e) => e.stopPropagation()}>
          <button onClick={() => setIsSettingsOpen(false)} className="close-panel-btn">&times;</button>
          <h2>Settings & Digest</h2>
          <div className="user-form">
            <label htmlFor="digest-day">Weekly Digest Day:</label>
            <select id="digest-day" value={digestDay} onChange={(e) => setDigestDay(e.target.value)}>
                {['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'].map(day => (
                    <option key={day} value={day}>{day}</option>
                ))}
            </select>
          </div>
          <div className="navigation-buttons">
            <button onClick={handleUpdatePreferences} disabled={isLoading} className="nav-button primary">{isLoading ? "Saving..." : "Save Preferences"}</button>
          </div>
          <hr className="divider" />
          <div className="digest-section">
            <h3>Generate Your Weekly Digest</h3>
            <p>Get a personalized summary of your best offers and smart tips from your AI co-pilot.</p>
            <button onClick={handleGenerateDigest} disabled={isLoading} className="nav-button secondary">{isLoading ? "Generating..." : "Generate Now"}</button>
            {weeklyDigest && (
              <div className="digest-content">
                <h3>{weeklyDigest.subject}</h3>
                <pre>{weeklyDigest.body}</pre>
              </div>
            )}
          </div>
        </div>
      </div>

      {message.text && <div className={`message ${message.type}`}>{message.text}</div>}
    </div>
  );
}

export default App;

