import { useState } from "react";
import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signInWithPopup,
  GoogleAuthProvider,
} from "firebase/auth";
import { auth } from "../firebase";

export default function AdminPage() {
  const [email, setEmail] = useState("test@test.com");
  const [password, setPassword] = useState("test123456");
  const [token, setToken] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const googleProvider = new GoogleAuthProvider();

  async function signInWithGoogle() {
  setLoading(true);
  setStatus("");
  setToken("");

  try {
    const cred = await signInWithPopup(auth, googleProvider);
    const idToken = await cred.user.getIdToken();

    setToken(idToken);
    setStatus(`Signed in with Google as ${cred.user.email || "user"}.`);
  } catch (e) {
    setStatus(e?.message || "Failed to sign in with Google.");
  } finally {
    setLoading(false);
  }
}

  async function createOrSignIn() {
    setLoading(true);
    setStatus("");
    setToken("");

    try {
      try {
        await createUserWithEmailAndPassword(auth, email, password);
        setStatus("User created successfully.");
      } catch (e) {
        setStatus("User probably already exists. Signing in...");
      }

      const cred = await signInWithEmailAndPassword(auth, email, password);
      const idToken = await cred.user.getIdToken();

      setToken(idToken);
      setStatus((prev) =>
        prev ? `${prev} Signed in successfully.` : "Signed in successfully."
      );
    } catch (e) {
      setStatus(e?.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  async function signInOnly() {
    setLoading(true);
    setStatus("");
    setToken("");

    try {
      const cred = await signInWithEmailAndPassword(auth, email, password);
      const idToken = await cred.user.getIdToken();
      setToken(idToken);
      setStatus("Signed in successfully.");
    } catch (e) {
      setStatus(e?.message || "Failed to sign in.");
    } finally {
      setLoading(false);
    }
  }

  async function copyToken() {
    if (!token) return;
    await navigator.clipboard.writeText(token);
    setStatus("Token copied to clipboard.");
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <h1 style={styles.h1}>Admin</h1>
        <p style={styles.subtle}>
          Create a Firebase email/password user for testing, then get the ID
          token for your API requests.
        </p>

        <label style={styles.label}>Email</label>
        <input
          style={styles.input}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="test@test.com"
        />

        <label style={styles.label}>Password</label>
        <input
          type="password"
          style={styles.input}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="test123456"
        />

        <div style={styles.row}>
          <button style={styles.button} onClick={createOrSignIn} disabled={loading}>
            {loading ? "Working..." : "Create user or sign in"}
          </button>

          <button style={styles.secondaryButton} onClick={signInOnly} disabled={loading}>
            Sign in only
          </button>
          <button
            style={styles.secondaryButton}
            onClick={signInWithGoogle}
            disabled={loading}
            >
            Sign in with Google
            </button>
        </div>

        {status ? <div style={styles.status}>{status}</div> : null}

        <label style={styles.label}>Firebase ID Token</label>
        <textarea
          style={styles.textarea}
          value={token}
          readOnly
          placeholder="Token will appear here after sign-in"
        />

        <button style={styles.secondaryButton} onClick={copyToken} disabled={!token}>
          Copy token
        </button>
      </div>
    </div>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    background: "#f5f7fb",
    padding: 24,
  },
  card: {
    maxWidth: 800,
    margin: "0 auto",
    background: "#fff",
    border: "1px solid #e5e7eb",
    borderRadius: 16,
    padding: 24,
  },
  h1: {
    marginTop: 0,
    marginBottom: 8,
  },
  subtle: {
    color: "#6b7280",
    marginBottom: 20,
  },
  label: {
    display: "block",
    marginTop: 12,
    marginBottom: 6,
    fontWeight: 600,
  },
  input: {
    width: "100%",
    padding: "10px 12px",
    borderRadius: 10,
    border: "1px solid #d1d5db",
    fontSize: 14,
    boxSizing: "border-box",
  },
  textarea: {
    width: "100%",
    minHeight: 220,
    padding: 12,
    borderRadius: 12,
    border: "1px solid #d1d5db",
    fontSize: 13,
    boxSizing: "border-box",
    resize: "vertical",
  },
  row: {
    display: "flex",
    gap: 12,
    marginTop: 16,
    marginBottom: 16,
  },
  button: {
    padding: "10px 14px",
    borderRadius: 10,
    border: "none",
    background: "#111827",
    color: "#fff",
    cursor: "pointer",
    fontWeight: 600,
  },
  secondaryButton: {
    padding: "10px 14px",
    borderRadius: 10,
    border: "1px solid #d1d5db",
    background: "#fff",
    color: "#111827",
    cursor: "pointer",
    fontWeight: 600,
  },
  status: {
    marginBottom: 16,
    padding: 12,
    borderRadius: 10,
    background: "#f3f4f6",
  },
};