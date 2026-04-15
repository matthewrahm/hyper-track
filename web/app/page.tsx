import Header from "./components/Header";
import LeaderboardTable from "./components/LeaderboardTable";

export default function Dashboard() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <Header />
      <LeaderboardTable />
    </div>
  );
}
