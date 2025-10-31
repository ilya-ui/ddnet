import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
from lmarena_api import LMArenaAPI


class ChatApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("LM Arena Chat - AI Assistant")
        self.root.geometry("900x700")
        self.root.minsize(600, 500)
        
        self.api = LMArenaAPI()
        self.is_processing = False
        
        self.setup_ui()
        self.apply_theme()
        
    def setup_ui(self):
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        header_frame = tk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = tk.Label(
            header_frame,
            text="🤖 LM Arena AI Chat",
            font=("Arial", 16, "bold")
        )
        title_label.pack(side=tk.LEFT)
        
        control_frame = tk.Frame(header_frame)
        control_frame.pack(side=tk.RIGHT)
        
        tk.Label(control_frame, text="Model:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.model_var = tk.StringVar(value="gpt-3.5-turbo")
        model_dropdown = ttk.Combobox(
            control_frame,
            textvariable=self.model_var,
            values=self.api.get_models(),
            state="readonly",
            width=15
        )
        model_dropdown.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_button = tk.Button(
            control_frame,
            text="🗑️ Clear Chat",
            command=self.clear_chat,
            font=("Arial", 9)
        )
        self.clear_button.pack(side=tk.LEFT)
        
        chat_frame = tk.Frame(main_container)
        chat_frame.pack(fill=tk.BOTH, expand=True)
        
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=("Arial", 11),
            state=tk.DISABLED,
            bg="#f5f5f5",
            padx=10,
            pady=10
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        self.chat_display.tag_config("user", foreground="#2196F3", font=("Arial", 11, "bold"))
        self.chat_display.tag_config("assistant", foreground="#4CAF50", font=("Arial", 11, "bold"))
        self.chat_display.tag_config("error", foreground="#F44336", font=("Arial", 11))
        self.chat_display.tag_config("message", font=("Arial", 11))
        
        input_frame = tk.Frame(main_container)
        input_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.message_input = tk.Text(
            input_frame,
            height=4,
            font=("Arial", 11),
            wrap=tk.WORD
        )
        self.message_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        self.message_input.bind("<Return>", self.on_enter_key)
        self.message_input.bind("<Shift-Return>", lambda e: None)
        
        button_frame = tk.Frame(input_frame)
        button_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.send_button = tk.Button(
            button_frame,
            text="📤 Send",
            command=self.send_message,
            font=("Arial", 11, "bold"),
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=10,
            cursor="hand2"
        )
        self.send_button.pack(fill=tk.BOTH, expand=True)
        
        status_frame = tk.Frame(main_container)
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.status_label = tk.Label(
            status_frame,
            text="Ready to chat",
            font=("Arial", 9),
            fg="#666"
        )
        self.status_label.pack(side=tk.LEFT)
        
    def apply_theme(self):
        style = ttk.Style()
        style.theme_use('clam')
        
    def on_enter_key(self, event):
        if not event.state & 0x1:
            self.send_message()
            return "break"
        return None
    
    def append_to_chat(self, text, tag=None):
        self.chat_display.config(state=tk.NORMAL)
        if tag:
            self.chat_display.insert(tk.END, text, tag)
        else:
            self.chat_display.insert(tk.END, text)
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
    def clear_chat(self):
        if messagebox.askyesno("Clear Chat", "Are you sure you want to clear the chat history?"):
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete(1.0, tk.END)
            self.chat_display.config(state=tk.DISABLED)
            self.api.reset_conversation()
            self.update_status("Chat cleared. Ready for new conversation.")
            
    def update_status(self, message):
        self.status_label.config(text=message)
        
    def send_message(self):
        if self.is_processing:
            return
            
        message = self.message_input.get("1.0", tk.END).strip()
        if not message:
            return
            
        self.message_input.delete("1.0", tk.END)
        
        self.is_processing = True
        self.send_button.config(state=tk.DISABLED, bg="#ccc")
        self.update_status("Sending message...")
        
        thread = threading.Thread(target=self.process_message, args=(message,))
        thread.daemon = True
        thread.start()
        
    def process_message(self, message):
        try:
            self.root.after(0, lambda: self.append_to_chat("You: ", "user"))
            self.root.after(0, lambda: self.append_to_chat(f"{message}\n\n", "message"))
            
            model = self.model_var.get()
            self.root.after(0, lambda: self.update_status(f"AI ({model}) is thinking..."))
            
            self.root.after(0, lambda: self.append_to_chat("Assistant: ", "assistant"))
            
            response_text = ""
            error_text = None
            for chunk in self.api.chat(message, model):
                if chunk.startswith("Error:") and not response_text:
                    error_text = chunk
                    break
                response_text += chunk
                self.root.after(0, lambda c=chunk: self.append_to_chat(c, "message"))
            
            if error_text:
                self.root.after(0, lambda c=error_text: self.append_to_chat(f"{c}\n\n", "error"))
                self.root.after(0, lambda: self.update_status("Error occurred"))
            else:
                if response_text:
                    self.root.after(0, lambda: self.append_to_chat("\n\n", "message"))
                    self.root.after(0, lambda: self.update_status("Ready to chat"))
                else:
                    self.root.after(0, lambda: self.append_to_chat("No response received.\n\n", "error"))
                    self.root.after(0, lambda: self.update_status("No response"))
            
        except Exception as e:
            error_msg = f"Error: {str(e)}\n\n"
            self.root.after(0, lambda: self.append_to_chat(error_msg, "error"))
            self.root.after(0, lambda: self.update_status("Error occurred"))
            
        finally:
            self.is_processing = False
            self.root.after(0, lambda: self.send_button.config(state=tk.NORMAL, bg="#4CAF50"))


def main():
    root = tk.Tk()
    app = ChatApplication(root)
    root.mainloop()


if __name__ == "__main__":
    main()
