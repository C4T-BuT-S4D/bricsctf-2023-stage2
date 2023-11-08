import ky, { HTTPError } from "ky";
import { useMutation, useQuery, useQueryClient } from "react-query";
import { notifications } from "@mantine/notifications";

type JsonError = {
  error: string;
};

async function handleMutationError(
  error: unknown,
  warningTitle: string,
  warningStatuses: number[]
) {
  if (
    error instanceof HTTPError &&
    warningStatuses.includes(error.response.status)
  ) {
    try {
      let jsonError: JsonError = await error.response.json();
      notifications.show({
        title: warningTitle,
        message: jsonError.error,
        color: "yellow",
      });
      return;
    } catch {}
  }

  notifications.show({
    title: "API Error",
    message: `${error}`,
    color: "red",
  });
}

export type Credentials = {
  username: string;
  password: string;
};

export function useRegister() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn(credentials: Credentials) {
      return ky
        .post("/api/register", {
          json: credentials,
        })
        .json<"">();
    },
    onError(error) {
      return handleMutationError(error, "Registration error", [409]);
    },
    onSuccess() {
      return queryClient.invalidateQueries({ queryKey: ["user"] });
    },
  });
}

export function useLogin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn(credentials: Credentials) {
      return ky
        .post("/api/login", {
          json: credentials,
        })
        .json<"">();
    },
    onError(error) {
      return handleMutationError(error, "Login error", [401]);
    },
    onSuccess() {
      return queryClient.invalidateQueries({ queryKey: ["user"] });
    },
  });
}

export type NotificationPlan = {
  planned_at: Date;
  sent_at: Date;
};

export type Notification = {
  id: string;
  title: string;
  content: string;
  plan: NotificationPlan[];
};

export type User = {
  username: string;
  notifications: Notification[];
};

export function useUser() {
  return useQuery("user", () => ky.get("/api/user").json<User>());
}
