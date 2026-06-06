import { Link, useLocation } from "react-router-dom";

const links = [
  { to: "/", label: "Classify" },
  { to: "/history", label: "History" },
];

export default function Navbar() {
  const { pathname } = useLocation();

  return (
    <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
      <Link to="/" className="text-xl font-bold text-gray-900">
        XplainCV
      </Link>
      <div className="flex gap-4">
        {links.map(({ to, label }) => (
          <Link
            key={to}
            to={to}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition ${
              pathname === to
                ? "bg-blue-100 text-blue-700"
                : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            {label}
          </Link>
        ))}
      </div>
    </nav>
  );
}
