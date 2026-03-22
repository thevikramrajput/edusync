import { getServerSession } from "next-auth";
import { authOptions } from "../../api/auth/[...nextauth]/route";

export default async function AdminDashboardPage() {
  const session = await getServerSession(authOptions);

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Admin Dashboard</h1>
      <div className="bg-white p-6 rounded-lg shadow-md border-t-4 border-red-600">
        <h2 className="text-xl font-semibold mb-2">Welcome back, {session?.user?.email}</h2>
        <p className="text-gray-600">This is the RED School EduOS Admin Control Panel.</p>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
          <div className="p-4 bg-gray-50 border border-gray-200 rounded">
            <h3 className="font-bold text-gray-700">Total Students</h3>
            <p className="text-2xl mt-2">1,250</p>
          </div>
          <div className="p-4 bg-gray-50 border border-gray-200 rounded">
            <h3 className="font-bold text-gray-700">Total Teachers</h3>
            <p className="text-2xl mt-2">84</p>
          </div>
          <div className="p-4 bg-gray-50 border border-gray-200 rounded">
            <h3 className="font-bold text-gray-700">Fee Collection</h3>
            <p className="text-2xl mt-2">₹12.5L</p>
          </div>
        </div>
      </div>
    </div>
  );
}
