require ["envelope", "reject"];

if not envelope :all :is "from" "notifier@notify" {
  reject "Only the notifier should send mail via this server.";
}
