import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";
import { authOptions } from "../api/auth/[...nextauth]/route";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await getServerSession(authOptions);

  if (!session) {
    redirect("/login");
  }

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col md:flex-row">
      {/* Sidebar Placeholder */}
      <aside className="w-full md:w-64 bg-red-700 text-white min-h-[100vh] flex flex-col">
        <div className="p-4 text-xl font-bold border-b border-red-500">
          RED School EduOS
        </div>
        <nav className="flex-1 p-4 space-y-2">
          <div>Role: {session?.user?.role}</div>
          <div>User: {session?.user?.email}</div>
          <hr className="my-4 border-red-500" />
          <a href="/dashboard" className="block p-2 hover:bg-red-600 rounded">Dashboard</a>
          {session?.user?.role === "ADMIN" && (
            <a href="/admin" className="block p-2 hover:bg-red-600 rounded">Admin Panel</a>
          )}
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-8">
        {children}
      </main>
    </div>
  );
}
