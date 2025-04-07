import React, { useState, useEffect, useCallback } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001';

function PostGenerator() {
    const [styles, setStyles] = useState([]);
    const [selectedStyleId, setSelectedStyleId] = useState('');
    const [topic, setTopic] = useState('');
    const [keyPoints, setKeyPoints] = useState(''); // Use textarea for multi-line points
    const [cta, setCta] = useState('');
    const [subjects, setSubjects] = useState(''); // New state for subjects/angles input
    const [generatedPosts, setGeneratedPosts] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [isFetchingStyles, setIsFetchingStyles] = useState(false);
    const [fetchError, setFetchError] = useState('');
    const [copiedIndex, setCopiedIndex] = useState(null); // Track which post was copied
    const [savingDraftIndex, setSavingDraftIndex] = useState(null); // Track saving state
    const [saveDraftStatus, setSaveDraftStatus] = useState({}); // Track status per draft index

    // Fetch styles function (wrapped in useCallback)
    const fetchStyles = useCallback(async () => {
        setIsFetchingStyles(true);
        setFetchError('');
        try {
            const response = await fetch(`${API_BASE_URL}/api/styles`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            setStyles(data);
            // Keep existing selection if possible, otherwise select first
            if (data.length > 0 && !data.find(s => s._id === selectedStyleId)) {
                 setSelectedStyleId(data[0]._id);
            } else if (data.length === 0) {
                setSelectedStyleId(''); // Reset if no styles
            }
        } catch (err) {
            console.error("Fetch Styles Error:", err);
            setFetchError(err.message || 'Failed to fetch styles.');
        } finally {
            setIsFetchingStyles(false);
        }
    }, [selectedStyleId]); // Dependency ensures it updates if selection becomes invalid

    // Fetch saved styles when the component mounts
    useEffect(() => {
        fetchStyles();
    }, [fetchStyles]); // Use the memoized fetchStyles

    const handleGenerateClick = async () => {
        setIsLoading(true);
        setError('');
        setGeneratedPosts([]);
        setCopiedIndex(null);
        setSavingDraftIndex(null); // Reset saving state
        setSaveDraftStatus({}); // Reset draft statuses

        // Basic validation
        if (!selectedStyleId || !topic.trim() || !keyPoints.trim()) {
            setError('Please select a style, enter a topic, and provide key points.');
            setIsLoading(false);
            return;
        }

        try {
            // Implement API call to /api/generate-post
            const payload = {
                style_id: selectedStyleId,
                topic: topic,
                key_points: keyPoints,
            };
            if (cta.trim()) { // Only include cta if it's not empty
                payload.cta = cta.trim();
            }
            // Add subjects/angles if provided
            if (subjects.trim()) {
                // Split by newline and filter empty lines
                payload.subjects_or_angles = subjects.split('\n').map(s => s.trim()).filter(s => s);
            }

            const response = await fetch(`${API_BASE_URL}/api/generate-post`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }

            // Set the received posts (expected to be an array)
            setGeneratedPosts(data.generated_posts || []);
            if (!data.generated_posts || data.generated_posts.length === 0) {
                setError("The AI didn't generate any post drafts. Try adjusting your inputs.");
            }

        } catch (err) {
            console.error("Generate Post Error:", err);
            setError(err.message || 'Failed to generate post. Please check the backend connection and try again.');
        } finally {
            setIsLoading(false);
        }
    };

    // Copy to clipboard function
    const handleCopyClick = (text, index) => {
        navigator.clipboard.writeText(text).then(() => {
            setCopiedIndex(index); // Set index of copied post
            setTimeout(() => setCopiedIndex(null), 2000); // Reset after 2 seconds
        }).catch(err => {
            console.error('Failed to copy text: ', err);
            // Optionally show an error message to the user
        });
    };

    // Save Draft function
    const handleSaveDraft = async (draftText, index) => {
        setSavingDraftIndex(index); // Show loading on the specific button
        setSaveDraftStatus(prev => ({ ...prev, [index]: 'Saving...' }));

        try {
            const payload = {
                draft_text: draftText,
                style_id: selectedStyleId, // Include context if available
                topic: topic
            };
            const response = await fetch(`${API_BASE_URL}/api/drafts`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }
            setSaveDraftStatus(prev => ({ ...prev, [index]: 'Saved!' }));
            console.log(`Draft ${index} saved with ID: ${data.draft_id}`);
        } catch (err) {
            console.error("Save Draft Error:", err);
            setSaveDraftStatus(prev => ({ ...prev, [index]: `Error: ${err.message}` }));
        } finally {
            setSavingDraftIndex(null); // Clear loading state for this button
            // Optionally clear status message after a delay
            setTimeout(() => {
                setSaveDraftStatus(prev => {
                    const newStatus = { ...prev };
                    // Only clear if it hasn't been overwritten by another attempt
                    if (newStatus[index] === 'Saved!' || newStatus[index]?.startsWith('Error:')) {
                         newStatus[index] = null;
                    }
                    return newStatus;
                });
            }, 3000);
        }
    };

    return (
        <div className="post-generator card">
            <h2>2. Generate New LinkedIn Post</h2>
            <p>Select one of your saved styles, provide a topic and key points, and optionally add specific angles or subjects (one per line) for the AI to explore using web search.</p>

            <div className="form-group">
                <label htmlFor="style-select">Select Style:</label>
                <div style={{ display: 'flex', alignItems: 'center' }}> {/* Flex container for select + button */}
                    <select
                        id="style-select"
                        value={selectedStyleId}
                        onChange={(e) => setSelectedStyleId(e.target.value)}
                        disabled={isFetchingStyles || styles.length === 0}
                        style={{ flexGrow: 1 }} // Allow select to grow
                    >
                        <option value="" disabled={styles.length > 0}>-- {isFetchingStyles ? "Loading..." : (styles.length === 0 ? "No Styles Saved Yet" : "Select a Style")} --</option>
                        {styles.map((style) => (
                            <option key={style._id} value={style._id}>
                                {style.name}
                            </option>
                        ))}
                    </select>
                    {/* Refresh Styles Button */}
                    <button onClick={fetchStyles} disabled={isFetchingStyles} className="button-secondary refresh-styles-button" title="Refresh Styles List">
                        &#x21bb; {/* Refresh symbol */}
                    </button>
                </div>
                {fetchError && <p className="error" style={{ marginTop: '0.5rem' }}>Error loading styles: {fetchError}</p>}
            </div>

            <div className="form-group">
                <label htmlFor="topic">Topic / Title:</label>
                <input
                    type="text"
                    id="topic"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="What is the main topic of your post?"
                    required
                />
            </div>

            <div className="form-group">
                <label htmlFor="key-points">Key Talking Points / Elements:</label>
                <textarea
                    id="key-points"
                    rows="5"
                    value={keyPoints}
                    onChange={(e) => setKeyPoints(e.target.value)}
                    placeholder="Enter key messages, bullet points, or ideas to include (one per line recommended)"
                    required
                />
            </div>

            <div className="form-group">
                <label htmlFor="subjects">Specific Subjects or Angles (Optional, 1 per line):</label>
                <textarea
                    id="subjects"
                    rows="3"
                    value={subjects}
                    onChange={(e) => setSubjects(e.target.value)}
                    placeholder="e.g., Impact on small business\nEthical considerations\nComparison with technology X"
                />
            </div>

            <div className="form-group">
                <label htmlFor="cta">Desired Call-to-Action (Optional):</label>
                <input
                    type="text"
                    id="cta"
                    value={cta}
                    onChange={(e) => setCta(e.target.value)}
                    placeholder="e.g., Link in comments, DM me, Visit website"
                />
            </div>

            {/* Optional: Add Target Audience input later if needed */}

            <button onClick={handleGenerateClick} disabled={isLoading || !selectedStyleId || !topic.trim() || !keyPoints.trim()} className="button-primary">
                {isLoading ? 'Generating...' : 'Generate Post Drafts'}
            </button>

            {error && <p className="error">{error}</p>}

            {generatedPosts.length > 0 && (
                <div className="generated-posts">
                    <h3>Generated Drafts:</h3>
                    {generatedPosts.map((post, index) => (
                        <div key={index} className="post-draft">
                            <pre>{post}</pre>
                            <div className="draft-actions">
                                {/* Save Draft Button */}
                                <button
                                    onClick={() => handleSaveDraft(post, index)}
                                    disabled={savingDraftIndex === index || saveDraftStatus[index] === 'Saved!'} // Disable if saving or already saved
                                    className="button-secondary save-draft-button"
                                >
                                    {savingDraftIndex === index ? 'Saving...' : (saveDraftStatus[index] === 'Saved!' ? 'Saved!' : 'Save Draft')}
                                </button>
                                {/* Copy Button */}
                                <button
                                    onClick={() => handleCopyClick(post, index)}
                                    className="copy-button button-secondary"
                                    disabled={copiedIndex === index} // Optionally disable briefly after copy
                                >
                                    {copiedIndex === index ? 'Copied!' : 'Copy'}
                                </button>
                                {saveDraftStatus[index] && saveDraftStatus[index] !== 'Saved!' && saveDraftStatus[index] !== 'Saving...' &&
                                    <span className="draft-save-error"> {saveDraftStatus[index]}</span>
                                }
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default PostGenerator;
