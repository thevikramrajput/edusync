/**
 * EduSync — Report Card Page.
 * Select student + exam → shows totals, percentage, grade.
 */
import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../api';

export default function ReportCardPage() {
    const [searchParams] = useSearchParams();
    const [studentId, setStudentId] = useState(searchParams.get('student_id') || '');
    const [examId, setExamId] = useState('');
    const [report, setReport] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const fetchReport = async () => {
        if (!studentId || !examId) {
            setError('Both Student ID and Exam ID are required.');
            return;
        }
        setError('');
        setLoading(true);
        try {
            const { data } = await api.get('/exams/marks/report-card/', {
                params: { student_id: studentId, exam_id: examId },
            });
            setReport(data.data);
        } catch (err) {
            setError(err.response?.data?.message || 'Failed to load report card.');
            setReport(null);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="page">
            <h1>📊 Report Card</h1>

            <div className="filters">
                <label>Student ID:</label>
                <input
                    type="text"
                    value={studentId}
                    onChange={(e) => setStudentId(e.target.value)}
                    placeholder="Paste Student UUID"
                    style={{ width: '300px' }}
                />

                <label style={{ marginLeft: '1rem' }}>Exam ID:</label>
                <input
                    type="text"
                    value={examId}
                    onChange={(e) => setExamId(e.target.value)}
                    placeholder="Paste Exam UUID"
                    style={{ width: '300px' }}
                />

                <button className="btn-primary" onClick={fetchReport} disabled={loading} style={{ marginLeft: '1rem' }}>
                    {loading ? 'Loading...' : 'Generate'}
                </button>
            </div>

            {error && <div className="error-msg">{error}</div>}

            {report && (
                <div className="card report-card">
                    <div className="report-header">
                        <h2>{report.student_name}</h2>
                        <p>Admission: {report.admission_number} | Exam: {report.exam_name}</p>
                    </div>

                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Subject</th>
                                <th>Marks Obtained</th>
                                <th>Max Marks</th>
                                <th>Percentage</th>
                            </tr>
                        </thead>
                        <tbody>
                            {report.subjects.map((sub, i) => (
                                <tr key={i}>
                                    <td>{sub.subject_name}</td>
                                    <td>{sub.marks_obtained}</td>
                                    <td>{sub.max_marks}</td>
                                    <td>{sub.percentage}%</td>
                                </tr>
                            ))}
                        </tbody>
                        <tfoot>
                            <tr className="total-row">
                                <td><strong>Total</strong></td>
                                <td><strong>{report.total_obtained}</strong></td>
                                <td><strong>{report.total_max}</strong></td>
                                <td><strong>{report.overall_percentage}%</strong></td>
                            </tr>
                        </tfoot>
                    </table>

                    <div className="grade-display">
                        <span className="grade-label">Grade:</span>
                        <span className="grade-value">{report.grade}</span>
                    </div>
                </div>
            )}
        </div>
    );
}
