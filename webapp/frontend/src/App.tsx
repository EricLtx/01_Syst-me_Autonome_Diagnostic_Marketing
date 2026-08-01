// App.tsx — routes du cockpit sous la coquille persistante.

import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { Prospects } from "./pages/Prospects";
import { ProspectDetail } from "./pages/ProspectDetail";
import { Usage } from "./pages/Usage";
import { Preflight } from "./pages/Preflight";

export function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/prospects" element={<Prospects />} />
        <Route path="/prospects/:slug" element={<ProspectDetail />} />
        <Route path="/usage" element={<Usage />} />
        <Route path="/preflight" element={<Preflight />} />
        <Route
          path="*"
          element={
            <div className="state-box">Page introuvable (404).</div>
          }
        />
      </Routes>
    </Layout>
  );
}
