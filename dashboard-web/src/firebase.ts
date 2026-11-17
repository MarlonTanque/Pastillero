import { initializeApp } from "firebase/app";
import {
  getAuth,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signOut,
  type User,
} from "firebase/auth";
import { ApiError, call, type AdminApi } from "./api";
import type { AccessRecord, AdminUser, Devices } from "./types";

/**
 * Cliente real: Firebase Authentication con la cuenta administrativa dedicada.
 * Solo usa la configuración web pública; nunca credenciales de servicio.
 */
export function firebaseApi(env: ImportMetaEnv): AdminApi {
  const app = initializeApp({
    apiKey: env.VITE_FIREBASE_API_KEY,
    authDomain: env.VITE_FIREBASE_AUTH_DOMAIN,
    projectId: env.VITE_FIREBASE_PROJECT_ID,
    appId: env.VITE_FIREBASE_APP_ID,
  });
  const auth = getAuth(app);
  const user = (): User => {
    if (!auth.currentUser)
      throw new ApiError(401, "INVALID_OR_REVOKED_SESSION");
    return auth.currentUser;
  };
  const token = () => user().getIdToken();
  return {
    demo: false,
    email: () => auth.currentUser?.email ?? null,
    async signIn(email, password) {
      const { user } = await signInWithEmailAndPassword(auth, email, password);
      // Comprobación de cortesía; el backend vuelve a exigir UID protegido + claim en cada petición.
      const { claims } = await user.getIdTokenResult(true);
      if (claims.dashboardAdmin !== true) {
        await signOut(auth);
        throw new ApiError(403, "DASHBOARD_ADMIN_REQUIRED");
      }
    },
    signOut: () => signOut(auth),
    onSession: (fn) => onAuthStateChanged(auth, (u) => fn(!!u)),
    async listUsers() {
      const users: AdminUser[] = [];
      let pageToken: string | null = null;
      do {
        const page: { users: AdminUser[]; nextPageToken: string | null } =
          await call(
            token,
            "GET",
            `/api/users${pageToken ? `?pageToken=${encodeURIComponent(pageToken)}` : ""}`,
          );
        users.push(...page.users);
        pageToken = page.nextPageToken;
      } while (pageToken);
      return users;
    },
    devices: () => call<Devices>(token, "GET", "/api/devices"),
    setAccess: (uid, enabled, expectedVersion) =>
      call<AccessRecord>(token, "PATCH", `/api/users/${uid}/access`, {
        enabled,
        expectedVersion,
      }),
    setFeatures: (uid, features, expectedVersion) =>
      call<AccessRecord>(token, "PATCH", `/api/users/${uid}/features`, {
        features,
        expectedVersion,
      }),
  };
}
