import React, { useState } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001';

// Helper component to display analysis items
function AnalysisItem({ label, value }) {
    if (!value) return null; // Don't render if value is empty/null

    let displayValue = value;
    if (Array.isArray(value)) {
        if (value.length === 0) return null;
        displayValue = <ul>{value.map((item, index) => <li key={index}>{item}</li>)}</ul>;
    } else if (typeof value === 'object' && value !== null) {
        displayValue = <pre>{JSON.stringify(value, null, 2)}</pre>; // Fallback for nested objects
    }

    return (
        <div className="analysis-item">
            <strong>{label}:</strong>
            <span>{displayValue}</span>
        </div>
    );
}

function StyleAnalyzer() {
    const [postsText, setPostsText] = useState('');
    const [analysisResult, setAnalysisResult] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [successMessage, setSuccessMessage] = useState('');

    const handleAnalyzeClick = async () => {
        setIsLoading(true);
        setError('');
        setAnalysisResult(null);
        setSuccessMessage('');

        if (postsText.trim().length < 100) {
            setError('Please paste more content (at least 100 characters) for a better analysis.');
            setIsLoading(false);
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/api/analyze-style`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ posts_text: postsText }),
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }
            setAnalysisResult(data.analysis);
            setSuccessMessage(data.message || 'Analysis complete.');
        } catch (err) {
            console.error("Analysis/Save Error:", err);
            setError(err.message || 'Failed to analyze and save style. Please check the backend connection and try again.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="style-analyzer card">
            <h2>1. Analyze & Save Your Writing Style</h2>
            <p>Paste 3-10 of your recent LinkedIn posts below. The AI will analyze them and automatically save the style profile with a suggested name.</p>
            <textarea
                rows="10" // Reduced rows slightly
                value={postsText}
                onChange={(e) => setPostsText(e.target.value)}
                placeholder="Paste your LinkedIn post content here..."
                aria-label="Paste LinkedIn posts here"
            />
            <br />
            <button onClick={handleAnalyzeClick} disabled={isLoading || !postsText.trim()} className="button-primary">
                {isLoading ? 'Analyzing & Saving...' : 'Analyze & Save Style'}
            </button>

            {error && <p className="error">{error}</p>}
            {successMessage && <p className="success">{successMessage}</p>}

            {analysisResult && (
                <div className="analysis-results">
                    <h4>Style Analysis Results (Saved as: "{analysisResult.style_name || 'Unnamed Style'}")</h4>
                    {/* Use helper component to display items */}
                    <AnalysisItem label="Overall Tone" value={analysisResult.overall_tone} />
                    <AnalysisItem label="Key Themes" value={analysisResult.key_themes} />
                    <AnalysisItem label="Common Keywords" value={analysisResult.common_keywords} />
                    <AnalysisItem label="Sentence Structure" value={analysisResult.sentence_structure} />
                    <AnalysisItem label="Emoji Usage" value={analysisResult.emoji_usage} />
                    <AnalysisItem label="Common CTA" value={analysisResult.common_cta} />
                    <AnalysisItem label="Perspective" value={analysisResult.perspective} />
                    {/* Optionally display other fields or the raw JSON as fallback */}
                    {/* <details>
                        <summary>Raw JSON</summary>
                        <pre>{JSON.stringify(analysisResult, null, 2)}</pre>
                    </details> */}
                </div>
            )}
        </div>
    );
}

export default StyleAnalyzer;
