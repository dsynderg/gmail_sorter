import os
import unittest

from gmail_api_helpers import (
    HttpError,
    get_message,
    list_history,
    list_labels,
    list_message_ids,
    pretty_http_error,
)


SEPARATOR = "-" * 70


def print_section(title: str) -> None:
    print(f"\n{SEPARATOR}")
    print(f"TEST: {title}")
    print(SEPARATOR)


def print_item(label: str, value) -> None:
    print(f"{label:<28}: {value}")


class PrettyTextTestResult(unittest.TextTestResult):
    def startTest(self, test):
        super().startTest(test)
        print(f"\n{SEPARATOR}\nRUNNING: {test._testMethodName}\n{SEPARATOR}")

    def addSuccess(self, test):
        super().addSuccess(test)
        print(f"✅ PASS: {test._testMethodName}")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        print(f"❌ FAIL: {test._testMethodName}")

    def addError(self, test, err):
        super().addError(test, err)
        print(f"💥 ERROR: {test._testMethodName}")

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        print(f"⏭️ SKIP: {test._testMethodName} ({reason})")


class PrettyTextTestRunner(unittest.TextTestRunner):
    resultclass = PrettyTextTestResult


class GmailApiProofTests(unittest.TestCase):
    def setUp(self):
        self.user_id = os.getenv("GMAIL_USER_EMAIL", "me")

    def test_list_message_ids(self):
        print_section("List Message IDs")
        try:
            message_ids = list_message_ids(user_id=self.user_id, max_results=100)
            print_item("User ID", self.user_id)
            print_item("Total Message IDs", len(message_ids))
            sample_ids = message_ids[:10]
            print_item("Sample IDs", sample_ids)
        except HttpError as error:
            self.fail(f"List message IDs failed: {pretty_http_error(error)}")

    def test_get_message_content(self):
        print_section("Get Message Content")
        try:
            message_ids = list_message_ids(user_id=self.user_id, max_results=1)
            if not message_ids:
                self.skipTest("No messages available to fetch.")
            message_id = message_ids[0]
            message = get_message(user_id=self.user_id, message_id=message_id, format="full")
            headers = {h["name"]: h.get("value") for h in message.get("payload", {}).get("headers", [])}
            print_item("User ID", self.user_id)
            print_item("Message ID", message_id)
            print_item("From", headers.get("From"))
            print_item("Subject", headers.get("Subject"))
        except HttpError as error:
            self.fail(f"Get message failed: {pretty_http_error(error)}")

    def test_list_labels(self):
        print_section("List Labels")
        try:
            labels = list_labels(user_id=self.user_id)
            names = [label.get("name") for label in labels]
            print_item("User ID", self.user_id)
            print_item("Total Labels", len(labels))
            print_item("Label Names", names)
        except HttpError as error:
            self.fail(f"List labels failed: {pretty_http_error(error)}")

    def test_list_history(self):
        print_section("List History")
        try:
            history = list_history(user_id=self.user_id, max_results=5)
            history_items = history.get("history", [])
            print_item("User ID", self.user_id)
            print_item("History Start ID", history.get("historyId"))
            print_item("History Record Count", len(history_items))
            if history_items:
                print_item("First Record Keys", list(history_items[0].keys()))
        except HttpError as error:
            self.fail(f"List history failed: {pretty_http_error(error)}")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(GmailApiProofTests)
    runner = PrettyTextTestRunner(verbosity=2)
    runner.run(suite)
