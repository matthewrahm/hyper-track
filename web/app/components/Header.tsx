import Link from "next/link";
import MethodologyModal from "./MethodologyModal";

export default function Header() {
  return (
    <header className="mb-8 flex items-center justify-between">
      <div>
        <Link href="/">
          <h1 className="text-2xl font-semibold tracking-tight text-primary">
            hyper-track
          </h1>
        </Link>
        <p className="mt-1 text-sm text-muted">
          Discover and track top Hyperliquid perp traders
        </p>
      </div>
      <MethodologyModal />
    </header>
  );
}
