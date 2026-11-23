"""Command-line entry point for the FitDesk enquiry assistant."""
from assistant import load_data, process_enquiry


def main():
    message = input("Customer message: ").strip()
    if not message:
        print("No message entered.")
        return
    data = load_data()
    status, _ = process_enquiry(message, data)
    print(f"Status recorded: {status}")


if __name__ == "__main__":
    main()