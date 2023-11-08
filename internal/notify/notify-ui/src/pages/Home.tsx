import {
  Accordion,
  AppShell,
  Badge,
  Box,
  Button,
  Center,
  Container,
  Group,
  Menu,
  Modal,
  Select,
  SimpleGrid,
  Space,
  Stack,
  Text,
  TextInput,
  Textarea,
  Timeline,
  Title,
  rem,
} from "@mantine/core";
import { DateTimePicker } from "@mantine/dates";
import { useForm } from "@mantine/form";
import { useDisclosure } from "@mantine/hooks";
import { IconChevronDown, IconDoor } from "@tabler/icons-react";
import React from "react";
import * as api from "../api";

type NotificationForm = {
  title: string;
  content: string;
  notifyAt: Date | null;
  repetitionCount: string | null;
  repetitionInterval: string;
};

export default function Home() {
  const [formOpened, { open: formOpen, close: formClose }] =
    useDisclosure(false);

  const notificationForm = useForm({
    initialValues: {
      title: "",
      content: "",
      notifyAt: null,
      repetitionCount: null,
      repetitionInterval: "10",
    } as NotificationForm,
    validate: {
      title(value) {
        if (value.length < 1) {
          return "Please add a title to be used as the subject of your notification";
        } else if (value.length > 50) {
          return "Sorry, but we can't store notifications with such long titles yet! Please shorten it.";
        }
      },
      content(value) {
        if (value.length < 1) {
          return "Please add the text which will be used as the body of your notification";
        } else if (value.length > 200) {
          return "Sorry, but we can't store notifications with such long texts yet! Please shorten the notification's contents.";
        }
      },
      notifyAt(value) {
        if (!value) {
          return "Specify the time you would like your notification to be sent at.";
        } else if (value < new Date(Date.now())) {
          return "Please use a time in the future as the notification time.";
        }
        return null;
      },
    },
  });

  const logout = api.useLogout();
  const createNotification = api.useCreateNotification();
  const { data } = api.useUser();

  data?.notifications
    .sort((a, b) => {
      let plannedA = a.plan[0].planned_at;
      let plannedB = b.plan[0].planned_at;

      if (plannedA < plannedB) {
        return -1;
      } else if (plannedA > plannedB) {
        return 1;
      }

      return 0;
    })
    .reverse();

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
            {data?.notifications && data.notifications.length > 0 ? (
              <Accordion className="w-[50vw]" variant="separated">
                {data.notifications.map((notification) => (
                  <Accordion.Item
                    key={notification.id}
                    value={notification.title}
                  >
                    <Accordion.Control>
                      <Group>
                        <Text>{notification.title} </Text>

                        {notification.plan[0].sent_at ? (
                          <Badge color="#22c55e">sent</Badge>
                        ) : (
                          <Badge color="#0ea5e9">planned</Badge>
                        )}
                      </Group>
                    </Accordion.Control>
                    <Accordion.Panel>
                      <SimpleGrid cols={2}>
                        <Timeline
                          active={
                            1 +
                            notification.plan.findLastIndex((plan) =>
                              Boolean(plan.sent_at)
                            )
                          }
                        >
                          {notification.plan.flatMap((plan, i) =>
                            i === 0
                              ? [
                                  <Timeline.Item
                                    key={`planned ${notification.id} ${plan.planned_at}`}
                                    title={`Planned`}
                                  >
                                    <Text
                                      c="dimmed"
                                      size="sm"
                                    >{`Planned to be sent at ${plan.planned_at.toLocaleString()}`}</Text>
                                  </Timeline.Item>,
                                  <Timeline.Item
                                    key={`sent ${notification.id} ${plan.planned_at}`}
                                    title={`Sent`}
                                  >
                                    <Text
                                      c={plan.sent_at ? "" : "dimmed"}
                                      size="sm"
                                    >
                                      {plan.sent_at
                                        ? `Actually sent at ${plan.sent_at.toLocaleString()}`
                                        : `Not sent yet`}
                                    </Text>
                                  </Timeline.Item>,
                                ]
                              : [
                                  <Timeline.Item
                                    key={`${notification.id} ${plan.planned_at}`}
                                    title={`Repetition ${i}`}
                                  >
                                    <Text
                                      c="dimmed"
                                      size="sm"
                                    >{`Planned to be sent at ${plan.planned_at.toLocaleString()}`}</Text>
                                    <Text
                                      c={plan.sent_at ? "" : "dimmed"}
                                      size="sm"
                                    >
                                      {plan.sent_at
                                        ? `Actually sent at ${plan.sent_at.toLocaleString()}`
                                        : `Not sent yet`}
                                    </Text>
                                  </Timeline.Item>,
                                ]
                          )}
                        </Timeline>
                        <Text size="lg">{notification.content}</Text>
                      </SimpleGrid>
                    </Accordion.Panel>
                  </Accordion.Item>
                ))}
              </Accordion>
            ) : (
              <React.Fragment>
                <Text size="xl">
                  You haven't created any notifications yet…
                </Text>
                <Text size="xl" className="pl-48">
                  …get started by planning one!
                </Text>
              </React.Fragment>
            )}

            <Space h="lg" />
            <Container size="sm">
              <Button
                size="lg"
                className="bg-gradient-to-tr from-sky-500 to-teal-300 hover:drop-shadow-md"
                onClick={() => {
                  formOpen();
                }}
              >
                Plan a new notification
              </Button>
            </Container>
          </Stack>
        </Center>

        <Modal opened={formOpened} onClose={formClose} title="New notification">
          <Box
            component="form"
            onSubmit={notificationForm.onSubmit((values) => {
              createNotification.mutate(
                {
                  title: values.title,
                  content: values.content,
                  notify_at: values.notifyAt!.toISOString(),
                  repetitions: values.repetitionCount
                    ? {
                        count: parseInt(values.repetitionCount),
                        interval: parseInt(values.repetitionInterval),
                      }
                    : undefined,
                },
                {
                  onSuccess() {
                    notificationForm.reset();
                    formClose();
                  },
                }
              );
            })}
          >
            <Stack>
              <TextInput
                label="Title"
                withAsterisk
                description="No more than 50 characters"
                placeholder="Water the flowers"
                {...notificationForm.getInputProps("title")}
              ></TextInput>
              <Textarea
                label="Content"
                withAsterisk
                description="No more than 200 characters"
                placeholder="Both in the garden and the living room."
                autosize={true}
                minRows={4}
                maxRows={4}
                {...notificationForm.getInputProps("content")}
              ></Textarea>
              <DateTimePicker
                label="Notify at"
                placeholder="Pick a date and time."
                withAsterisk
                {...notificationForm.getInputProps("notifyAt")}
              ></DateTimePicker>
              <Select
                label="Additionally repeat"
                placeholder="Do not repeat"
                data={[{ value: "1", label: "1 time" }].concat(
                  [...Array(19).keys()].map((i) => ({
                    value: `${i + 2}`,
                    label: `${i + 2} times`,
                  }))
                )}
                clearable
                {...notificationForm.getInputProps("repetitionCount")}
              ></Select>
              {notificationForm.values["repetitionCount"] ? (
                <Select
                  label="Every"
                  withAsterisk
                  data={[
                    { value: "10", label: "10 seconds" },
                    { value: "30", label: "30 seconds" },
                    { value: "60", label: "minute" },
                    { value: "600", label: "10 minutes" },
                    { value: "1800", label: "half an hour" },
                    { value: "3600", label: "hour" },
                  ]}
                  allowDeselect={false}
                  {...notificationForm.getInputProps("repetitionInterval")}
                ></Select>
              ) : (
                <React.Fragment></React.Fragment>
              )}
              <Group justify="flex-end" mt="md">
                <Button
                  type="submit"
                  className="bg-gradient-to-tr from-sky-500 to-teal-300 hover:drop-shadow-md"
                >
                  Create
                </Button>
              </Group>
            </Stack>
          </Box>
        </Modal>
      </AppShell.Main>
    </AppShell>
  );
}
