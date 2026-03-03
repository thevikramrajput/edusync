/**
 * EduSync — Student List Page.
 * Paginated, searchable, filterable by class.
 */
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';

export default function StudentListPage() {
    const [students, setStudents] = useState([]);
    const [search, setSearch] = useState('');
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [loading, setLoading] = useState(false);

    const fetchStudents = async () => {
        setLoading(true);
        try {
            const params = { page, search: search || undefined };
            const { data } = await api.get('/auth/students/', { params });
            setStudents(data.results || []);
            setTotalPages(Math.ceil((data.count || 0) / 10));
        } catch (err) {
            console.error('Failed to fetch students:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchStudents(); }, [page, search]);

    return (
        <div className="page">
            <div className="page-header">
                <h1>Students</h1>
            </div>

            <div className="filters">
                <input
                    type="text"
                    placeholder="Search by name or admission number..."
                    value={search}
                    onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                />
            </div>

            {loading ? (
                <p>Loading...</p>
            ) : (
                <>
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Admission #</th>
                                <th>Name</th>
                                <th>Class</th>
                                <th>Section</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {students.length === 0 ? (
                                <tr><td colSpan="5" className="empty">No students found.</td></tr>
                            ) : (
                                students.map((s) => (
                                    <tr key={s.id}>
                                        <td>{s.admission_number}</td>
                                        <td>{s.full_name || `${s.first_name} ${s.last_name}`}</td>
                                        <td>{s.class_name || '—'}</td>
                                        <td>{s.section_name || '—'}</td>
                                        <td>
                                            <Link to={`/students/${s.id}`} className="btn-sm">View</Link>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>

                    <div className="pagination">
                        <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}>← Prev</button>
                        <span>Page {page} of {totalPages}</span>
                        <button disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Next →</button>
                    </div>
                </>
            )}
        </div>
    );
}
