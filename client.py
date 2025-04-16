#!/usr/bin/env python3
import grpc
import chatbot_pb2
import chatbot_pb2_grpc
import logging
import uuid
import datetime
import threading
import queue
import sys
import time
import os
import json

# Configure logging - Change from INFO to ERROR level to suppress info messages
logging.basicConfig(level=logging.INFO)

def get_timestamp():
    """Helper function to get current timestamp in ISO format"""
    return datetime.datetime.now().isoformat()

def run():
    # Create a gRPC channel
    with grpc.insecure_channel('localhost:50051') as channel:
        # Create a stub (client)
        stub = chatbot_pb2_grpc.ChatServiceStub(channel)
        
        print("\nMira AI Assistant - gRPC Demo")
        print("==============================")
        print("Choose a communication type:")
        print("1. Unary RPC - Single question and answer")
        print("2. Server Streaming - Get response in chunks")
        print("3. Client Streaming - Submit URLs for bulk summarization")
        print("4. Bidirectional Streaming - Interactive chat session with history")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == "1":
            unary_communication(stub)
        elif choice == "2":
            server_streaming(stub)
        elif choice == "3":
            client_streaming(stub)
        elif choice == "4":
            bidirectional_streaming(stub)
        elif choice == "5":
            print("\nGoodbye!")
            return
        else:
            print("\nInvalid choice. Please try again.")
            run()

def unary_communication(stub):
    """Unary RPC - Summarize 1 URL or respond to 1 question"""
    print("\nUnary RPC Demo - Ask a question or request a URL summary")
    print("(type 'quit' to return to menu)")
    
    while True:
        user_input = input("\nYou: ")
        
        # Exit condition
        if user_input.lower() in ['quit', 'exit', 'back']:
            run()
            break
        
        # Skip empty messages
        if not user_input.strip():
            continue
        
        try:
            # Create a request
            request = chatbot_pb2.ChatRequest(user_message=user_input)
            
            # Make the gRPC call
            response = stub.GetReply(request)
            
            # Print the response
            print(f"\nAI: {response.ai_response}")
            
        except grpc.RpcError as e:
            status_code = e.code()
            details = e.details()
            logging.error(f"RPC error: {status_code}, {details}")
            print(f"\nError communicating with server: {status_code}, {details}")
        except Exception as e:
            logging.error(f"Error: {str(e)}")
            print(f"\nAn error occurred: {str(e)}")

def server_streaming(stub):
    """Server Streaming RPC - Stream chatbot response in parts"""
    print("\nServer Streaming Demo - Get AI responses in chunks")
    print("(type 'quit' to return to menu)")
    
    while True:
        user_input = input("\nYou: ")
        
        # Exit condition
        if user_input.lower() in ['quit', 'exit', 'back']:
            run()
            break
        
        # Skip empty messages
        if not user_input.strip():
            continue
        
        try:
            # Create a request
            request = chatbot_pb2.ChatRequest(user_message=user_input)
            
            # Make the streaming gRPC call
            responses = stub.StreamResponse(request)
            
            print("\nAI: ", end="")
            sys.stdout.flush()  # Ensure the prompt appears without newline
            
            # Process each chunk as it arrives
            for response in responses:
                print(response.content, end=" ")
                sys.stdout.flush()  # Ensure chunk is displayed immediately
                
                # If this is the final chunk, add a newline
                if response.is_final:
                    print()  # Add a newline at the end
            
        except grpc.RpcError as e:
            status_code = e.code()
            details = e.details()
            logging.error(f"RPC error: {status_code}, {details}")
            print(f"\nError communicating with server: {status_code}, {details}")
        except Exception as e:
            logging.error(f"Error: {str(e)}")
            print(f"\nAn error occurred: {str(e)}")

def client_streaming(stub):
    """Client Streaming RPC - Send multiple URLs to summarize in bulk"""
    print("\nClient Streaming Demo - Submit multiple URLs for bulk summarization")
    print("Enter URLs one by one. When finished, type 'done'.")
    print("(type 'quit' to return to menu)")
    
    urls = []
    
    # Collect URLs from user
    while True:
        url_input = input("\nEnter URL (or 'done' when finished): ")
        
        # Exit conditions
        if url_input.lower() in ['quit', 'exit', 'back']:
            run()
            return
        
        if url_input.lower() == 'done':
            if not urls:
                print("No URLs entered. Please enter at least one URL.")
                continue
            break
        
        # Skip empty inputs
        if not url_input.strip():
            continue
        
        # Get optional max length parameter
        max_length = input("Max summary length (words, press Enter for default): ")
        max_length = int(max_length) if max_length.strip() and max_length.isdigit() else 100
        
        # Add URL to the list
        urls.append((url_input, max_length))
        print(f"Added URL: {url_input} (max length: {max_length} words)")
    
    try:
        # Create a generator for the client stream
        def request_generator():
            for url, max_length in urls:
                yield chatbot_pb2.UrlRequest(url=url, max_length=max_length)
        
        # Make the client streaming gRPC call
        print("\nSubmitting URLs for summarization...")
        response = stub.BulkSummarize(request_generator())
        
        # Process the response
        print(f"\nProcessed {response.total_processed} URLs:")
        
        for i, summary in enumerate(response.summaries, 1):
            print(f"\n--- Summary {i} ---")
            print(f"URL: {summary.url}")
            if summary.success:
                print(f"Summary: {summary.summary}")
            else:
                print(f"Error: {summary.error_message}")
        
        input("\nPress Enter to return to the menu...")
        run()
        
    except grpc.RpcError as e:
        status_code = e.code()
        details = e.details()
        logging.error(f"RPC error: {status_code}, {details}")
        print(f"\nError communicating with server: {status_code}, {details}")
        input("\nPress Enter to return to the menu...")
        run()
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        print(f"\nAn error occurred: {str(e)}")
        input("\nPress Enter to return to the menu...")
        run()

def bidirectional_streaming(stub):
    """Bidirectional Streaming RPC - Real-time chat with history and session management"""
    print("\nBidirectional Streaming Demo - Interactive chat session with history")
    print("(type 'quit' to return to menu)")
    
    # Set up a queue for outgoing messages
    outgoing_queue = queue.Queue()
    
    # Set up a flag to signal the sending thread to stop
    stop_event = threading.Event()
    
    # Load or create user and session information
    user_id, session_id = load_user_session()
    print(f"User ID: {user_id}")
    if session_id:
        print(f"Continuing previous session: {session_id}")
    else:
        print("Starting new chat session")
    
    # For displaying chat history/context
    message_history = []
    
    # Create a lock for console output to prevent overlapping prints
    console_lock = threading.Lock()
    
    # Thread function for sending messages
    def send_messages():
        try:
            # Create a generator that yields messages from the queue
            def message_generator():
                while not stop_event.is_set():
                    try:
                        message = outgoing_queue.get(block=True, timeout=0.1)
                        yield message
                        outgoing_queue.task_done()
                    except queue.Empty:
                        continue
            
            # Start the bidirectional streaming RPC
            responses = stub.ChatSession(message_generator())
            
            # Process incoming messages
            for response in responses:
                if stop_event.is_set():
                    break
                
                # Update session_id if this is the first response
                nonlocal session_id
                if not session_id and response.session_id:
                    with console_lock:
                        session_id = response.session_id
                        save_user_session(user_id, session_id)
                        print(f"\nNew session created: {session_id}")
                
                # Save message to history
                message_history.append({
                    "sender": response.sender,
                    "text": response.text,
                    "timestamp": response.timestamp
                })
                
                # Display the response with proper formatting
                with console_lock:
                    print(f"\nAI: {response.text}")
                    # Re-display the input prompt
                    sys.stdout.write("\nYou: ")
                    sys.stdout.flush()
                
        except grpc.RpcError as e:
            if not stop_event.is_set():  # Only log if not intentionally stopping
                status_code = e.code()
                details = e.details()
                logging.error(f"RPC error: {status_code}, {details}")
                with console_lock:
                    print(f"\nError communicating with server: {status_code}, {details}")
                    sys.stdout.write("\nYou: ")
                    sys.stdout.flush()
        except Exception as e:
            if not stop_event.is_set():  # Only log if not intentionally stopping
                logging.error(f"Error: {str(e)}")
                with console_lock:
                    print(f"\nAn error occurred: {str(e)}")
                    sys.stdout.write("\nYou: ")
                    sys.stdout.flush()
    
    # Start the sending thread
    send_thread = threading.Thread(target=send_messages)
    send_thread.daemon = True
    send_thread.start()
    
    try:
        # Get username if not already set
        if user_id == "anonymous":
            username = input("\nEnter your name (or press Enter to stay anonymous): ")
            if username.strip():
                user_id = username
                save_user_session(user_id, session_id)
        
        # Print chat commands help
        print("\nChat Commands:")
        print("  /help     - Show these commands")
        print("  /clear    - Start a new session")
        print("  /history  - Show conversation history")
        print("  /quit     - Return to main menu")
        
        # Main loop for getting user input
        while True:
            # Use a consistent prompt format
            user_input = input("\nYou: ")
            
            # Process special commands
            if user_input.lower() in ['/quit', 'quit', 'exit', 'back']:
                stop_event.set()  # Signal the thread to stop
                time.sleep(1)  # Give it time to clean up
                run()
                break
            
            elif user_input.lower() == '/help':
                with console_lock:
                    print("\nChat Commands:")
                    print("  /help     - Show these commands")
                    print("  /clear    - Start a new session")
                    print("  /history  - Show conversation history")
                    print("  /quit     - Return to main menu")
                continue
                
            elif user_input.lower() == '/clear':
                with console_lock:
                    session_id = None
                    message_history.clear()
                    save_user_session(user_id, session_id)
                    print("\nStarting a new chat session")
                continue
                
            elif user_input.lower() == '/history':
                with console_lock:
                    print("\n=== Conversation History ===")
                    if not message_history:
                        print("No messages in this session yet")
                    else:
                        for i, msg in enumerate(message_history):
                            prefix = "AI:  " if msg["sender"] == "ai" else "You: "
                            print(f"{i+1}. {prefix}{msg['text']}")
                    print("===========================")
                continue
            
            # Skip empty messages
            if not user_input.strip():
                continue
            
            # Create a chat message
            message = chatbot_pb2.ChatMessage(
                text=user_input,
                sender="user",
                timestamp=get_timestamp(),
                message_id=str(uuid.uuid4()),
                reply_to="",  # No specific message to reply to
                session_id=session_id,
                user_id=user_id
            )
            
            # Save message to history
            message_history.append({
                "sender": "user",
                "text": user_input,
                "timestamp": get_timestamp()
            })
            
            # Add the message to the outgoing queue
            outgoing_queue.put(message)
            
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        # Make sure we signal the thread to stop
        stop_event.set()
        # Save the session information before exiting
        save_user_session(user_id, session_id)
        send_thread.join(timeout=2)
        run()

def load_user_session():
    """Load user and session information from a file"""
    session_file = os.path.expanduser("~/.mira_chat_session.json")
    
    try:
        if os.path.exists(session_file):
            with open(session_file, 'r') as f:
                data = json.load(f)
                return data.get("user_id", "anonymous"), data.get("session_id", None)
    except Exception as e:
        logging.error(f"Error loading session data: {str(e)}")
    
    return "anonymous", None

def save_user_session(user_id, session_id):
    """Save user and session information to a file"""
    session_file = os.path.expanduser("~/.mira_chat_session.json")
    
    try:
        with open(session_file, 'w') as f:
            json.dump({
                "user_id": user_id,
                "session_id": session_id,
                "last_updated": get_timestamp()
            }, f)
    except Exception as e:
        logging.error(f"Error saving session data: {str(e)}")

if __name__ == '__main__':
    try:
        run()
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        print(f"\nAn unexpected error occurred: {str(e)}")