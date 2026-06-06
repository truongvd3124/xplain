import { NavLink } from 'react-router-dom'

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `rounded-md px-3 py-2 text-sm font-medium ${
    isActive ? 'bg-indigo-600 text-white' : 'text-slate-600 hover:bg-slate-200'
  }`

export default function Navbar() {
  return (
    <nav className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl items-center gap-6 px-4 py-3">
        <span className="text-lg font-bold text-indigo-700">XplainScreen</span>
        <div className="flex gap-2">
          <NavLink to="/builder" className={linkClass}>
            Profile Builder
          </NavLink>
          <NavLink to="/verify" className={linkClass}>
            Verify
          </NavLink>
          <NavLink to="/" end className={linkClass}>
            Screening Dashboard
          </NavLink>
        </div>
      </div>
    </nav>
  )
}
