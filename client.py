#!/usr/bin/env python3
import grpc
import chatbot_pb2
import chatbot_pb2_grpc
import logging

# Configure logging - Change from INFO to ERROR level to suppress info messages
logging.basicConfig(level=logging.ERROR)

def run():
    # Create a gRPC channel
    with grpc.insecure_channel('localhost:50051') as channel:
        # Create a stub (client)
        stub = chatbot_pb2_grpc.ChatServiceStub(channel)
        
        print("Mira AI Assistant (type 'quit' to exit)")
        print("-------------------------------------")
        
        # Interactive loop
        while True:
            user_input = input("\nYou: ")
            
            # Exit condition
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\nGoodbye!")
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

if __name__ == '__main__':
    run()