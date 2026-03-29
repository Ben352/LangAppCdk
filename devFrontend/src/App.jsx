import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import ChatPage from "./pages/ChatPage";
import AdminPage from "./pages/AdminPage";

export default function App() {
  return (
    <BrowserRouter>
      <div style={styles.nav}>
        <Link style={styles.link} to="/">Chat</Link>
        <Link style={styles.link} to="/admin">Admin</Link>
      </div>

      <Routes>
        <Route path="/" element={<ChatPage />} />
        <Route path="/admin" element={<AdminPage />} />
      </Routes>
    </BrowserRouter>
  );
}

const styles = {
  nav: {
    display: "flex",
    gap: 16,
    padding: "12px 20px",
    borderBottom: "1px solid #e5e7eb",
    background: "#fff",
  },
  link: {
    textDecoration: "none",
    fontWeight: 600,
    color: "#111827",
  },
};