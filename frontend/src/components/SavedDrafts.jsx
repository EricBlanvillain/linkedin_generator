import React, { useState, useEffect, useCallback } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001';

function SavedDrafts() {
    const [drafts, setDrafts] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [deletingId, setDeletingId] = useState(null);

    // Fetch drafts function
    const fetchDrafts = useCallback(async () => {
        setIsLoading(true);
        setError('');
        try {
            const response = await fetch(`${API_BASE_URL}/api/drafts`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            setDrafts(data);
        } catch (err) {
            console.error("Fetch Drafts Error:", err);
            setError(err.message || 'Failed to fetch saved drafts.');
        } finally {
            setIsLoading(false);
        }
    }, []);

    // Fetch on mount
    useEffect(() => {
        fetchDrafts();
    }, [fetchDrafts]);

    // Handle delete click
    const handleDelete = async (draftId) => {
        if (!window.confirm(`Are you sure you want to delete this draft?`)) {
            return;
        }
        setDeletingId(draftId);
        setError('');
        try {
            const response = await fetch(`${API_BASE_URL}/api/drafts/${draftId}`, {
                method: 'DELETE',
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }
            setDrafts(prevDrafts => prevDrafts.filter(draft => draft._id !== draftId));
            console.log(`Draft ${draftId} deleted.`);
        } catch (err) {
            console.error("Delete Draft Error:", err);
            setError(err.message || 'Failed to delete draft.');
        } finally {
            setDeletingId(null);
        }
    };

    // Helper to format date
    const formatDate = (dateString) => {
        try {
            return new Date(dateString).toLocaleString();
        } catch (e) {
            return dateString; // Return original if parsing fails
        }
    }

    return (
        <div className="saved-drafts card">
            <h2>Saved Drafts</h2>
            <p>Manage your saved post drafts here.</p>

            {isLoading && <p>Loading drafts...</p>}
            {error && <p className="error">{error}</p>}

            {!isLoading && drafts.length === 0 && (
                <p><i>No drafts saved yet. Generate some posts and click 'Save Draft'!</i></p>
            )}

            {drafts.length > 0 && (
                <ul className="drafts-list">
                    {drafts.map((draft) => (
                        <li key={draft._id}>
                            <div className="draft-content">
                                <p className="draft-topic">Topic: {draft.topic || 'N/A'}</p>
                                <pre className="draft-text-preview">{draft.draft_text}</pre>
                                <p className="draft-date">Saved: {formatDate(draft.created_at)}</p>
                            </div>
                            <div className="draft-actions-list">
                                <button
                                    onClick={() => handleDelete(draft._id)}
                                    disabled={deletingId === draft._id}
                                    className="button-secondary delete-button"
                                >
                                    {deletingId === draft._id ? 'Deleting...' : 'Delete'}
                                </button>
                                {/* TODO: Add Edit/Copy functionality here? */}
                            </div>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}

export default SavedDrafts;
