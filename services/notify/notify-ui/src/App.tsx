import { notifications } from "@mantine/notifications";
import * as api from "./api";
import Welcome from "./pages/Welcome";
import Home from "./pages/Home";
import { HTTPError } from "ky";
import { LoadingOverlay } from "@mantine/core";
import React from "react";

export default function App() {
  const { isLoading, isError, data, error } = api.useUser();

  const authError = error instanceof HTTPError && error.response.status == 401;

  if (data && !authError) {
    return <Home></Home>;
  }

  if (!isLoading && isError) {
    if (!authError) {
      notifications.show({
        title: "API Error",
        message: `${error}`,
        color: "red",
      });
    }
  }

  return (
    <React.Fragment>
      <LoadingOverlay visible={isLoading}></LoadingOverlay>
      <Welcome></Welcome>
    </React.Fragment>
  );
}
