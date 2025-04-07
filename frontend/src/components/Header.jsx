import React from 'react';
import { NavLink } from 'react-router-dom';
import './Header.css'; // We'll create this CSS file next

function Header() {
    return (
        <header className="app-nav-header">
            <nav>
                <ul>
                    <li>
                        <NavLink to="/analyze" className={({ isActive }) => isActive ? 'active' : ''}>
                            Analyze Style
                        </NavLink>
                    </li>
                    <li>
                        <NavLink to="/generate" className={({ isActive }) => isActive ? 'active' : ''}>
                            Generate Post
                        </NavLink>
                    </li>
                    <li>
                        <NavLink to="/styles" className={({ isActive }) => isActive ? 'active' : ''}>
                            Saved Styles
                        </NavLink>
                    </li>
                    <li>
                        <NavLink to="/drafts" className={({ isActive }) => isActive ? 'active' : ''}>
                            Saved Drafts
                        </NavLink>
                    </li>
                    {/* Add more navigation items here if needed */}
                </ul>
            </nav>
        </header>
    );
}

export default Header;
