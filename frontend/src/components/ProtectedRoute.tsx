// Guards routes that require authentication (and optionally a specific role).
// If the user is not logged in, they are redirected to /login.
// If allowedRoles is provided and the user's role is not in the list, they see a 403 message.

import { Navigate } from "react-router-dom";
import { Result, Button } from "antd";

import { useAuth } from "../store/AuthContext";

interface ProtectedRouteProps {
  children: React.ReactNode;
  // Optional: restrict access to specific roles. If omitted, any authenticated user is allowed.
  allowedRoles?: string[];
}

export default function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const { isAuthenticated, user } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    return (
      <Result
        status="403"
        title="Access Denied"
        subTitle="You don't have permission to view this page."
        extra={
          <Button type="primary" onClick={() => window.history.back()}>
            Go Back
          </Button>
        }
      />
    );
  }

  return <>{children}</>;
}
