from imapclient import IMAPClient
import email
from email.header import decode_header
import getpass

def connect_to_imap(host, username, password):
    server = IMAPClient(host, use_uid=True)
    server.login(username, password)
    return server

def list_folders(server):
    folders = server.list_folders()
    for folder in folders:
        server.select_folder(folder[2])
        unread_count = len(server.search(['UNSEEN']))
        print(f"Folder: {folder[2]}, Unread: {unread_count}")

def fetch_unread_emails(server, folder, mark_as_read=False):
    server.select_folder(folder)
    messages = server.search(['UNSEEN'])

    for msg_id in messages:
        raw_message = server.fetch([msg_id], ['BODY[]', 'FLAGS'])
        email_message = email.message_from_bytes(raw_message[msg_id][b'BODY[]'])

        subject = decode_header(email_message['Subject'])[0][0]
        if isinstance(subject, bytes):
            subject = subject.decode()

        from_ = decode_header(email_message['From'])[0][0]
        if isinstance(from_, bytes):
            from_ = from_.decode()

        print(f"Subject: {subject}")
        print(f"From: {from_}")
        print("--------------------")

        if mark_as_read:
            server.add_flags([msg_id], ['\\Seen'])

def main():
    host = input("Enter IMAP server address: ")
    username = input("Enter your email address: ")
    password = getpass.getpass("Enter your password: ")

    server = connect_to_imap(host, username, password)

    while True:
        print("\n1. List folders with unread email count")
        print("2. Fetch unread emails from a specific folder")
        print("3. Exit")
        choice = input("Enter your choice (1-3): ")

        if choice == '1':
            list_folders(server)
        elif choice == '2':
            folder = input("Enter the folder name: ")
            mark_as_read = input("Mark fetched emails as read? (y/n): ").lower() == 'y'
            fetch_unread_emails(server, folder, mark_as_read)
        elif choice == '3':
            break
        else:
            print("Invalid choice. Please try again.")

    server.logout()

if __name__ == "__main__":
    main()

