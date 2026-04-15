import Header from "./components/Header";
import DiscoverPanel from "./components/DiscoverPanel";
import LeaderboardTable from "./components/LeaderboardTable";

export default function Dashboard() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <Header />
      <DiscoverPanel />
      <LeaderboardTable />
    </div>
  );
}
