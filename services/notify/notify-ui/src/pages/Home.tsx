import { AppShell, Button, Title } from "@mantine/core";
import * as api from "../api";

export default function Home() {
  const logout = api.useLogout();

  return (
    <AppShell header={{ height: 64 }} padding="md">
      <AppShell.Header className="bg-sky-100 flex justify-between items-center px-16">
        <Title order={1}>Notify</Title>
        <Button
          size="md"
          className="bg-red-100 hover:drop-shadow-md w-32 text-red-500 border-red-500"
          onClick={() => {
            logout.mutate();
          }}
        >
          Logout
        </Button>
      </AppShell.Header>
      <AppShell.Main></AppShell.Main>
    </AppShell>
  );
}
