import { NavLink } from "react-router-dom";

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `px-4 py-2 text-sm font-medium rounded-lg transition ${
    isActive
      ? "bg-blue-600 text-white"
      : "text-gray-600 hover:bg-gray-100"
  }`;

export default function Navbar() {
  return (
    <nav className="bg-white border-b border-gray-200">
      <div className="max-w-4xl mx-auto px-6 py-3 flex items-center gap-6">
        <span className="font-bold text-gray-900">XplainCV</span>
        <div className="flex gap-2">
          <NavLink to="/" end className={linkClass}>
            1 · Builder
          </NavLink>
          <NavLink to="/verify" className={linkClass}>
            2 · Verify
          </NavLink>
        </div>
      </div>
    </nav>
  );
}
