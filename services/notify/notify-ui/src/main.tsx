import "@mantine/core/styles.css";
import "@mantine/notifications/styles.css";
import "./index.css";

import { MantineProvider } from "@mantine/core";
import { Notifications } from "@mantine/notifications";
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.tsx";
import { theme } from "./theme";
import { QueryClient, QueryClientProvider } from "react-query";
import { HTTPError } from "ky";

const queryClient = new QueryClient();
queryClient.setDefaultOptions({
  queries: {
    retry(_, error) {
      if (error instanceof HTTPError && error.response.status == 401) {
        return false;
      }

      return true;
    },
  },
});

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <MantineProvider theme={theme}>
        <Notifications position="bottom-right" autoClose={8000} />
        <App />
      </MantineProvider>
    </QueryClientProvider>
  </React.StrictMode>
);
