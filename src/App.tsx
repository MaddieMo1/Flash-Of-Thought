import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { Layout } from "@/components/Layout";
import RecordIdea from "@/pages/RecordIdea";
import KnowledgeReview from "@/pages/KnowledgeReview";
import KnowledgeGraph from "@/pages/KnowledgeGraph";

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard/record" replace />} />
        
        <Route path="/dashboard" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard/record" replace />} />
          <Route path="record" element={<RecordIdea />} />
          <Route path="review" element={<KnowledgeReview />} />
          <Route path="graph" element={<KnowledgeGraph />} />
          <Route path="favorites" element={<div className="p-8">收藏 - Coming Soon</div>} />
          <Route path="history" element={<div className="p-8">历史记录 - Coming Soon</div>} />
          <Route path="settings" element={<div className="p-8">设置 - Coming Soon</div>} />
        </Route>
      </Routes>
    </Router>
  );
}
