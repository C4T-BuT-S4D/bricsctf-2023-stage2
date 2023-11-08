import {
  AppShell,
  Badge,
  Button,
  Center,
  Container,
  Group,
  Space,
  Stack,
  Title,
  Text,
  Menu,
  rem,
} from "@mantine/core";
import * as api from "../api";
import { useDisclosure } from "@mantine/hooks";
import { IconChevronDown, IconDoor } from "@tabler/icons-react";

export default function Home() {
  const [formOpened, { open: formOpen, close: formClose }] =
    useDisclosure(false);

  const logout = api.useLogout();
  const { data } = api.useUser();

  return (
    <AppShell header={{ height: 64 }} padding="md">
      <AppShell.Header className="bg-sky-100 flex justify-between items-center px-16">
        <Title order={1}>Notify</Title>
        <Group>
          <Menu
            trigger="hover"
            openDelay={100}
            closeDelay={400}
            transitionProps={{ transition: "rotate-right", duration: 150 }}
            shadow="md"
            width={200}
          >
            <Menu.Target>
              <Badge color="#0ea5e9" size="xl">
                <Group gap="xs">
                  {data?.username + "@notify"}
                  <IconChevronDown />
                </Group>
              </Badge>
            </Menu.Target>
            <Menu.Dropdown>
              <Menu.Item
                color="red"
                leftSection={<IconDoor style={{ marginRight: rem(16) }} />}
                rightSection={<Text>Logout</Text>}
                className="hover:drop-shadow-md"
                onClick={() => {
                  logout.mutate();
                }}
              ></Menu.Item>
            </Menu.Dropdown>
          </Menu>
        </Group>
      </AppShell.Header>
      <AppShell.Main>
        <Center>
          <Stack>
            <Space />
            <Container size="sm">
              <Text size="xl">You haven't created any notifications yet…</Text>
              <Text size="xl" className="pl-48">
                …get started by planning one!
              </Text>
            </Container>
            <Space h="lg" />
            <Button
              size="lg"
              className="bg-gradient-to-tr from-sky-500 to-teal-300 hover:drop-shadow-md"
              onClick={() => {
                formOpen();
              }}
            >
              Plan a new notification
            </Button>
          </Stack>
        </Center>
      </AppShell.Main>
    </AppShell>
  );
}
