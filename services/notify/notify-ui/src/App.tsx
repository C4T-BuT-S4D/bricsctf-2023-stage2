import {
  AppShell,
  Button,
  Center,
  Container,
  Image,
  Modal,
  Space,
  Stack,
  Text,
  Tabs,
  Title,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { useState } from "react";

export default function App() {
  const [authOpened, { open: authOpen, close: authClose }] =
    useDisclosure(false);
  const [authTab, setAuthTab] = useState<string | null>("register");

  return (
    <AppShell header={{ height: 64 }} padding="md">
      <AppShell.Header className="bg-sky-100 flex justify-between items-center px-16">
        <Title order={1}>Notify</Title>
        <Button.Group>
          <Button
            size="md"
            className="bg-gradient-to-tr from-sky-500 to-teal-300 hover:drop-shadow-md w-32"
            onClick={() => {
              setAuthTab("register");
              authOpen();
            }}
          >
            Register
          </Button>
          <Button
            size="md"
            className="bg-sky-400 hover:drop-shadow-md w-32"
            onClick={() => {
              setAuthTab("login");
              authOpen();
            }}
          >
            Login
          </Button>
        </Button.Group>
      </AppShell.Header>
      <AppShell.Main>
        <Center>
          <Stack>
            <Space />
            <Container size="sm">
              <Text size="xl">
                Tired of those pesky notifications always popping up on your
                phone?
              </Text>
            </Container>
            <Space h="lg" />
            <Container size="sm">
              <Text size="xl" fw={700}>
                So are we!
              </Text>
            </Container>
            <Container size="sm">
              <Text size="lg" className="text-center">
                Which is why we built Notify. A reliable, old-school
                notification system which delivers whatever you desire and
                whenever you desire directly to your beloved mail agent!
              </Text>
            </Container>
            <Image src="/preview.png" h={600} w="auto" fit="contain"></Image>
          </Stack>

          <Modal.Root opened={authOpened} onClose={authClose}>
            <Modal.Overlay />
            <Modal.Content>
              <Tabs value={authTab} onChange={setAuthTab}>
                <Modal.Header>
                  <Tabs.List
                    className="w-full"
                    justify="space-evenly"
                    grow={true}
                  >
                    <Tabs.Tab value="register">Register</Tabs.Tab>
                    <Tabs.Tab value="login">Login</Tabs.Tab>
                  </Tabs.List>
                </Modal.Header>
                <Modal.Body>
                  <Tabs.Panel value="register">Registration</Tabs.Panel>
                  <Tabs.Panel value="login">Login</Tabs.Panel>
                </Modal.Body>
              </Tabs>
            </Modal.Content>
          </Modal.Root>
        </Center>
      </AppShell.Main>
    </AppShell>
  );
}
