#!/usr/bin/env python3
import sys
from lmarena_api import LMArenaAPI


def main():
    print("=" * 60)
    print("LM Arena Chat - CLI Version")
    print("=" * 60)
    print()
    
    api = LMArenaAPI()
    models = api.get_models()
    
    print("Available models:")
    for i, model in enumerate(models, 1):
        print(f"  {i}. {model}")
    print()
    
    model_choice = input(f"Select model (1-{len(models)}) [default: 2 (gpt-3.5-turbo)]: ").strip()
    if model_choice and model_choice.isdigit():
        model_idx = int(model_choice) - 1
        if 0 <= model_idx < len(models):
            selected_model = models[model_idx]
        else:
            selected_model = "gpt-3.5-turbo"
    else:
        selected_model = "gpt-3.5-turbo"
    
    print(f"\nUsing model: {selected_model}")
    print("Type 'quit' or 'exit' to end the chat, 'clear' to reset conversation\n")
    print("-" * 60)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['quit', 'exit']:
                print("\nGoodbye!")
                break
                
            if user_input.lower() == 'clear':
                api.reset_conversation()
                print("Conversation cleared.")
                continue
            
            print(f"\nAssistant ({selected_model}): ", end="", flush=True)
            
            response_text = ""
            for chunk in api.chat(user_input, selected_model):
                print(chunk, end="", flush=True)
                response_text += chunk
            
            if not response_text:
                print("(No response)")
            
            print()
            print("-" * 60)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("-" * 60)


if __name__ == "__main__":
    main()
