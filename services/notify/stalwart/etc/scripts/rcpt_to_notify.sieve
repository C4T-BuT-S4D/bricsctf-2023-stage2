require ["envelope", "reject"];

if not envelope :domain :is "to" "notify" {
  reject "Only mail to notify addresses is accepted.";
}

if envelope :all :is "to" "notifier@notify" {
  reject "Only mail to non-service users is accepted.";
}
