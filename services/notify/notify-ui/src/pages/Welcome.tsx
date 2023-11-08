import {
  AppShell,
  Box,
  Button,
  Center,
  Container,
  Group,
  Image,
  Modal,
  PasswordInput,
  Space,
  Stack,
  Tabs,
  Text,
  TextInput,
  Title,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { useDisclosure } from "@mantine/hooks";
import { useState } from "react";
import * as api from "../api";

export default function Welcome() {
  const [authOpened, { open: authOpen, close: authClose }] =
    useDisclosure(false);
  const [authTab, setAuthTab] = useState<string | null>("register");

  const authForm = useForm({
    initialValues: {
      username: "",
      password: "",
    },
    validate: {
      username: (value) => {
        if (!/^[a-z][a-z0-9_-]+[a-z0-9]$/.test(value)) {
          return "We currently allow usernames consisting only of lowercase english letters, numbers, and dashes/underscores in between the rest! Sorry!";
        }

        if (value.length < 5) {
          return "Your username is too short! Please make it at least 5 characters long.";
        } else if (value.length > 15) {
          return "Your username is too long! Please shorten it to 15 characters or less.";
        }
      },
      password: (value) => {
        if (value.length < 8) {
          return "Please lengthen your password to at least 8 characters, it is dangerously short right now!";
        } else if (value.length > 30) {
          return "Your password is very long, please shorten it to 30 characters or less.";
        }
      },
    },
  });

  const register = api.useRegister();
  const login = api.useLogin();

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
                  <Tabs.Panel value="register">
                    <Box
                      component="form"
                      onSubmit={authForm.onSubmit((values) =>
                        register.mutate(values)
                      )}
                    >
                      <Stack>
                        <TextInput
                          label="Username"
                          withAsterisk
                          description="Between 5 and 15 characters"
                          placeholder="Your preferred account username"
                          {...authForm.getInputProps("username")}
                        />
                        <PasswordInput
                          label="Password"
                          withAsterisk
                          description="From 8 to 30 of any characters"
                          placeholder="Secure password"
                          {...authForm.getInputProps("password")}
                        />
                        <Group justify="flex-end" mt="md">
                          <Button
                            type="submit"
                            className="bg-gradient-to-tr from-sky-500 to-teal-300 hover:drop-shadow-md"
                          >
                            Submit
                          </Button>
                        </Group>
                      </Stack>
                    </Box>
                  </Tabs.Panel>
                  <Tabs.Panel value="login">
                    <Box
                      component="form"
                      onSubmit={authForm.onSubmit((values) =>
                        login.mutate(values)
                      )}
                    >
                      <Stack>
                        <TextInput
                          label="Username"
                          withAsterisk
                          description="Between 5 and 15 characters"
                          placeholder="The username you have registered with"
                          {...authForm.getInputProps("username")}
                        />
                        <PasswordInput
                          label="Password"
                          withAsterisk
                          description="From 8 to 30 of any characters"
                          placeholder="Your password"
                          {...authForm.getInputProps("password")}
                        />
                        <Group justify="flex-end" mt="md">
                          <Button
                            type="submit"
                            className="bg-gradient-to-tr from-sky-500 to-teal-300 hover:drop-shadow-md"
                          >
                            Submit
                          </Button>
                        </Group>
                      </Stack>
                    </Box>
                  </Tabs.Panel>
                </Modal.Body>
              </Tabs>
            </Modal.Content>
          </Modal.Root>
        </Center>
      </AppShell.Main>
    </AppShell>
  );
}
