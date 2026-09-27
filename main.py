from game import Game


def main():
    try:
        name = input("Enter your player's name: ")
        game = Game(name)
        while True:
            state = game.snapshot()
            print(f"\n{state['name']} | Health: {state['health']}/{state['max_health']} | Scene {state['scene']}")
            for message in state["messages"]:
                print(message)
            if state["outcome"]:
                break
            print(f"\n{state['prompt']}")
            for index, option in enumerate(state["options"], 1):
                print(f"{index}. {option['label']}")
            choice = input("> ").strip()
            try:
                index = int(choice) - 1
            except ValueError:
                print("Please enter the number of an available choice.")
                continue
            if not 0 <= index < len(state["options"]):
                print("Invalid choice.")
                continue
            game.choose(state["options"][index]["id"])
    except (EOFError, KeyboardInterrupt):
        print("\nThe game session ended.")


if __name__ == "__main__":
    main()
