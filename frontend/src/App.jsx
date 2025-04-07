import React from 'react';
import {
    BrowserRouter as Router,
    Routes,
    Route,
    Navigate
} from 'react-router-dom';
import Header from './components/Header'; // Import Header
import StyleAnalyzer from './components/StyleAnalyzer';
import PostGenerator from './components/PostGenerator';
import SavedStyles from './components/SavedStyles'; // Placeholder
import SavedDrafts from './components/SavedDrafts'; // Placeholder
import './App.css'; // Keep basic styling

function App() {
    return (
        <Router>
            <div className="App">
                <header className="App-header">
                    <h1>LinkedIn Style Syncer & Post Generator</h1>
                </header>

                <Header />

                <main>
                    <Routes>
                        <Route path="/analyze" element={<StyleAnalyzer />} />

                        <Route path="/generate" element={<PostGenerator />} />

                        <Route path="/styles" element={<SavedStyles />} />

                        <Route path="/drafts" element={<SavedDrafts />} />

                        <Route path="*" element={<Navigate to="/analyze" replace />} />
                    </Routes>
                </main>
            </div>
        </Router>
    );
}

export default App;
