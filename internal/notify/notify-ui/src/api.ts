import { notifications } from "@mantine/notifications";
import ky, { HTTPError } from "ky";
import { useMutation, useQuery, useQueryClient } from "react-query";

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

export function useLogout() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn() {
      return ky.post("/api/logout").json<"">();
    },
    onError(error) {
      return handleMutationError(error, "", []);
    },
    onSuccess() {
      return queryClient.invalidateQueries({ queryKey: ["user"] });
    },
  });
}

export type CreateNotificationRepetitions = {
  count: number;
  interval: number;
};

export type CreateNotificationRequest = {
  title: string;
  content: string;
  notify_at: string;
  repetitions?: CreateNotificationRepetitions;
};

export function useCreateNotification() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn(notification: CreateNotificationRequest) {
      return ky.post("/api/notifications", { json: notification }).json<"">();
    },
    onError(error) {
      return handleMutationError(error, "", [422]);
    },
    onSuccess() {
      return queryClient.invalidateQueries({ queryKey: ["user"] });
    },
  });
}

export type NotificationPlan = {
  planned_at: Date;
  sent_at: Date | null;
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
  return useQuery("user", async () => {
    let response = await ky.get("/api/user").json<User>();
    response.notifications.forEach((notification) => {
      notification.plan = notification.plan.map((plan) => ({
        planned_at: new Date(plan.planned_at),
        sent_at: plan.sent_at ? new Date(plan.sent_at) : null,
      }));
    });
    return response;
  });
}
