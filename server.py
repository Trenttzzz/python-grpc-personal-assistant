#!/usr/bin/env python3
import os
import grpc
import chatbot_pb2
import chatbot_pb2_grpc
import concurrent.futures
from concurrent import futures
import logging
from groq import Groq

# Configure logging
logging.basicConfig(level=logging.INFO)

# You'll need to set your Groq API key as an environment variable
# export GROQ_API_KEY=your_api_key_here

class ChatServicer(chatbot_pb2_grpc.ChatServiceServicer):
    def __init__(self):
        # Initialize Groq client
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            logging.error("GROQ_API_KEY environment variable is not set")
            raise ValueError("GROQ_API_KEY environment variable is not set")
        self.client = Groq(api_key=api_key)
        
    def GetReply(self, request, context):
        logging.info(f"Received message: {request.user_message}")
        
        try:
            # Call the Groq API with the user's message
            chat_completion = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",  # You can change this to another model if needed
                messages=[
                    {"role": "system", "content": "You are mira, a helpful assistant."},
                    {"role": "user", "content": request.user_message}
                ]
            )
            
            # Extract the response from the API result
            ai_response = chat_completion.choices[0].message.content
            logging.info(f"Generated response: {ai_response}")
            
            return chatbot_pb2.ChatReply(ai_response=ai_response)
        
        except Exception as e:
            logging.error(f"Error calling Groq API: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error processing request: {str(e)}")
            return chatbot_pb2.ChatReply(ai_response="Sorry, I encountered an error processing your request.")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chatbot_pb2_grpc.add_ChatServiceServicer_to_server(ChatServicer(), server)
    server_address = '[::]:50051'
    server.add_insecure_port(server_address)
    server.start()
    logging.info(f"Server started, listening on {server_address}")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()