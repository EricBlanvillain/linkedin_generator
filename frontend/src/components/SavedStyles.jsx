import React, { useState, useEffect, useCallback } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001';

function SavedStyles() {
    const [styles, setStyles] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [deletingId, setDeletingId] = useState(null); // Track which style is being deleted

    // Fetch styles function
    const fetchStyles = useCallback(async () => {
        setIsLoading(true);
        setError('');
        try {
            const response = await fetch(`${API_BASE_URL}/api/styles`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            setStyles(data);
        } catch (err) {
            console.error("Fetch Styles Error:", err);
            setError(err.message || 'Failed to fetch saved styles.');
        } finally {
            setIsLoading(false);
        }
    }, []);

    // Fetch on mount
    useEffect(() => {
        fetchStyles();
    }, [fetchStyles]);

    // Handle delete click
    const handleDelete = async (styleId, styleName) => {
        // Optional: Add confirmation dialog
        if (!window.confirm(`Are you sure you want to delete the style "${styleName}"?`)) {
            return;
        }

        setDeletingId(styleId); // Indicate loading state for this item
        setError(''); // Clear previous errors

        try {
            const response = await fetch(`${API_BASE_URL}/api/styles/${styleId}`, {
                method: 'DELETE',
            });

            const data = await response.json(); // Even errors might return JSON

            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }

            // Remove deleted style from state
            setStyles(prevStyles => prevStyles.filter(style => style._id !== styleId));
            console.log(`Style ${styleId} deleted.`);
            // Optionally show a success message

        } catch (err) {
            console.error("Delete Style Error:", err);
            setError(err.message || 'Failed to delete style.');
        } finally {
            setDeletingId(null); // Reset loading state for this item
        }
    };

    return (
        <div className="saved-styles card">
            <h2>Saved Styles</h2>
            <p>Manage your saved writing styles here. Click delete to remove a style.</p>

            {isLoading && <p>Loading styles...</p>}
            {error && <p className="error">{error}</p>}

            {!isLoading && styles.length === 0 && (
                <p><i>No styles saved yet. Analyze some posts to create your first style!</i></p>
            )}

            {styles.length > 0 && (
                <ul className="styles-list">
                    {styles.map((style) => (
                        <li key={style._id}>
                            <span>{style.name}</span>
                            <button
                                onClick={() => handleDelete(style._id, style.name)}
                                disabled={deletingId === style._id} // Disable button while deleting this specific item
                                className="button-secondary delete-button"
                            >
                                {deletingId === style._id ? 'Deleting...' : 'Delete'}
                            </button>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}

export default SavedStyles;
