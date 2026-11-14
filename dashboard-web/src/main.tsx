import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { demoApi } from "./demo";
import { firebaseApi } from "./firebase";
import "./styles.css";

// Sin configuración web de Firebase se abre la demostración con datos ficticios.
const api = import.meta.env.VITE_FIREBASE_API_KEY
  ? firebaseApi(import.meta.env)
  : demoApi();
createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App api={api} />
  </StrictMode>,
);
