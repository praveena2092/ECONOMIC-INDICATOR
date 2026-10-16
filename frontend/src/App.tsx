import { AuthProvider, useAuth } from "./auth/AuthContext";
import { LoginPage } from "./auth/LoginPage";
import { Dashboard } from "./components/Dashboard";

function Gate() {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <Dashboard /> : <LoginPage />;
}

export default function App() {
  return <AuthProvider><Gate /></AuthProvider>;
}
