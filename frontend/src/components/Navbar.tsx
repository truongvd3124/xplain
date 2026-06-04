import { NavLink } from "react-router-dom";

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `relative px-4 py-2 text-sm font-semibold rounded-xl transition-all duration-300 ${
    isActive
      ? "text-white btn-grad"
      : "text-[var(--ink-soft)] hover:text-[var(--ink)] hover:bg-black/[0.04]"
  }`;

export default function Navbar() {
  return (
    <nav className="sticky top-0 z-30 glass border-x-0 border-t-0">
      <div className="max-w-5xl mx-auto px-6 py-3 flex items-center gap-6">
        <div className="flex items-center gap-2.5 select-none">
          <img
            src="/logo.png"
            alt="XplainCV logo"
            className="w-9 h-9 object-contain mix-blend-multiply"
          />
          <span className="text-lg font-extrabold tracking-tight text-[var(--ink)]">
            Xplain<span className="text-gradient">CV</span>
          </span>
        </div>

        <div className="flex gap-1.5 ml-auto sm:ml-0">
          <NavLink to="/" end className={linkClass}>
            <span className="relative z-10">1 · Builder</span>
          </NavLink>
          <NavLink to="/verify" className={linkClass}>
            <span className="relative z-10">2 · Verify</span>
          </NavLink>
        </div>

        <span className="hidden sm:block ml-auto text-xs font-medium text-[var(--ink-soft)]/70">
          Zero-shot Concept Bottleneck
        </span>
      </div>
    </nav>
  );
}
