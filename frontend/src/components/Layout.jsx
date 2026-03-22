/**
 * EduSync — Layout with Sidebar Navigation.
 */
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Layout() {
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = async () => {
        await logout();
        navigate('/login');
    };

    return (
        <div className="app-layout">
            <aside className="sidebar">
                <div className="sidebar-header">
                    <h2>📚 EduSync</h2>
                    <span className="user-role">{user?.role_type}</span>
                </div>
                <nav>
                    <NavLink to="/" end>🏠 Dashboard</NavLink>
                    <NavLink to="/students">👨‍🎓 Students</NavLink>
                    <NavLink to="/exam-marks">📝 Exam Marks</NavLink>
                    <NavLink to="/report-card">📊 Report Card</NavLink>
                    <NavLink to="/assessments">📋 Assessments</NavLink>
                </nav>
                <div className="sidebar-footer">
                    <p>{user?.full_name}</p>
                    <p className="email">{user?.email}</p>
                    <button className="btn-logout" onClick={handleLogout}>Logout</button>
                </div>
            </aside>
            <main className="main-content">
                <Outlet />
            </main>
        </div>
    );
}
