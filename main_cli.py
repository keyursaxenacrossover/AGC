import os
from securityagent import analyze_images, run_security_check
from orchestrator import orchestrate
from contexter import update_context
from config import imagedir


def main():
    context_so_far = ""  # Initialize context for the first chat

    while True:  # Allow multiple chat turns
        user_question = input("Enter your question or request (or type 'exit' to quit): ")
        if user_question.lower() == "exit":
            print("Exiting...")
            break

        # Analyze images
        image_descriptions = analyze_images(imagedir)
        print(f"Image Analysis:\n{image_descriptions}\n")

        # Run security check
        result = run_security_check(user_question, image_descriptions)
        print("=== Security Check Result ===")
        print(result)

        if result["malicious"] == "Y":
            # Handle malicious input
            malicious_reason = result["final_response"].split("MALICIOUS: ")[-1]
            print(f"Malicious input detected: {malicious_reason}")
        else:
            # Prepare the full input for orchestrator
            full_user_input = (
                f"The user provided this text input:\n{result['user_input']}\n\n"
                f"The user also provided these images:\n" + "\n".join(result['image_descriptions'])
            )

            # Send non-malicious input to orchestrator
            print("No malicious input detected. Querying orchestrator...")
            orchestrator_result = orchestrate(full_user_input, context_so_far)
            print("=== Orchestrator Response ===")
            print(orchestrator_result)

            # Update context for the next chat turn
            interaction_data = {
                "context_so_far": context_so_far,
                "user_text_input": result["user_input"],
                "user_image_descriptions": result["image_descriptions"],
                "response_to_user": orchestrator_result,
            }
            context_so_far = update_context(interaction_data)

            # Print the updated context
            print("\n=== Updated Context ===")
            print(context_so_far)


if __name__ == "__main__":
    main()
