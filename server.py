#!/usr/bin/env python3
import os
import grpc
import chatbot_pb2
import chatbot_pb2_grpc
import concurrent.futures
from concurrent import futures
import logging
from groq import Groq
import time
import uuid
from datetime import datetime
import threading

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
        
        # Session storage for conversation history
        self.sessions = {}
        self.sessions_lock = threading.Lock()
        
    def GetReply(self, request, context):
        """Unary RPC - Summarize 1 URL or respond to 1 question"""
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
    
    def StreamResponse(self, request, context):
        """Server Streaming RPC - Stream chatbot response in parts"""
        logging.info(f"Received stream request: {request.user_message}")
        
        try:
            # Call the Groq API with the user's message
            chat_completion = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are mira, a helpful assistant."},
                    {"role": "user", "content": request.user_message}
                ]
            )
            
            # Extract the response from the API result
            ai_response = chat_completion.choices[0].message.content
            logging.info(f"Generated response for streaming: {ai_response}")
            
            # Split the response into chunks (sentences or paragraphs)
            # For demonstration, we'll split by sentences
            chunks = ai_response.split('. ')
            total_chunks = len(chunks)
            
            for i, chunk in enumerate(chunks):
                # Add period back if this isn't the last chunk
                if i < total_chunks - 1 and not chunk.endswith('.'):
                    chunk += '.'
                    
                # Add a small delay to simulate streaming
                time.sleep(0.5)
                
                # Determine if this is the final chunk
                is_final = (i == total_chunks - 1)
                
                # Yield each chunk as a separate response
                yield chatbot_pb2.ResponseChunk(content=chunk.strip(), is_final=is_final)
                
        except Exception as e:
            logging.error(f"Error in streaming response: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error processing streaming request: {str(e)}")
            # We need to yield an error response since this is a streaming RPC
            yield chatbot_pb2.ResponseChunk(
                content=f"Sorry, I encountered an error processing your request: {str(e)}",
                is_final=True
            )
    
    def BulkSummarize(self, request_iterator, context):
        """Client Streaming RPC - Send multiple URLs to summarize in bulk"""
        logging.info("Started bulk URL summarization process")
        
        summaries = []
        count = 0
        
        # Process each URL request from the client stream
        for request in request_iterator:
            count += 1
            url = request.url
            max_length = request.max_length if request.max_length > 0 else 100  # Default length
            
            logging.info(f"Processing URL {count}: {url}")
            
            try:
                # For demonstration, we'll simulate URL summarization
                # In a real implementation, you would fetch and analyze the URL content
                
                # Call the Groq API to generate a summary
                prompt = f"Summarize the content of this URL: {url} in about {max_length} words."
                
                chat_completion = self.client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": "You are a summarization assistant."},
                        {"role": "user", "content": prompt}
                    ]
                )
                
                summary = chat_completion.choices[0].message.content
                
                # Add the summary to our results
                summaries.append(chatbot_pb2.UrlSummary(
                    url=url,
                    summary=summary,
                    success=True,
                    error_message=""
                ))
                
            except Exception as e:
                logging.error(f"Error summarizing URL {url}: {str(e)}")
                summaries.append(chatbot_pb2.UrlSummary(
                    url=url,
                    summary="",
                    success=False,
                    error_message=str(e)
                ))
        
        logging.info(f"Completed processing {count} URLs")
        return chatbot_pb2.BulkSummaryResponse(
            summaries=summaries,
            total_processed=count
        )
    
    def ChatSession(self, request_iterator, context):
        """Bidirectional Streaming RPC - Real-time chatbot with history"""
        logging.info("Started bidirectional chat session")
        
        session_id = None
        user_id = None
        
        try:
            # Process incoming messages from the client
            for request in request_iterator:
                # Get or create session for this conversation
                if session_id is None:
                    session_id = request.session_id if request.session_id else str(uuid.uuid4())
                    user_id = request.user_id if request.user_id else "anonymous"
                    
                    # Initialize session if it doesn't exist
                    with self.sessions_lock:
                        if session_id not in self.sessions:
                            logging.info(f"Creating new session {session_id} for user {user_id}")
                            self.sessions[session_id] = {
                                "user_id": user_id,
                                "created_at": datetime.now().isoformat(),
                                "last_active": datetime.now().isoformat(),
                                "messages": [
                                    {"role": "system", "content": "You are mira, a helpful assistant. Maintain conversation context and provide relevant, coherent responses."}
                                ]
                            }
                        else:
                            logging.info(f"Resuming existing session {session_id} for user {user_id}")
                
                # Record timestamp for the message
                timestamp = datetime.now().isoformat()
                
                # Log the incoming message
                logging.info(f"Received chat message in session {session_id}: {request.text}")
                
                # Update session
                with self.sessions_lock:
                    # Update last activity time
                    self.sessions[session_id]["last_active"] = timestamp
                    
                    # Add the user message to chat history
                    self.sessions[session_id]["messages"].append({
                        "role": "user",
                        "content": request.text
                    })
                    
                    # Keep only the last 20 messages to prevent context size issues
                    if len(self.sessions[session_id]["messages"]) > 21:  # 1 system prompt + 20 conversation turns
                        # Keep the system message and the 19 most recent conversation messages
                        self.sessions[session_id]["messages"] = [
                            self.sessions[session_id]["messages"][0]  # System message
                        ] + self.sessions[session_id]["messages"][-19:]  # Last 19 conversation messages
                
                # Generate a unique message ID for the AI response
                response_id = str(uuid.uuid4())
                
                # Create a response message based on the chat history
                try:
                    # Get the current session messages for context
                    with self.sessions_lock:
                        messages = self.sessions[session_id]["messages"].copy()
                    
                    # Call the Groq API with the full chat history
                    chat_completion = self.client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=messages
                    )
                    
                    ai_response = chat_completion.choices[0].message.content
                    
                    # Add the AI response to chat history
                    with self.sessions_lock:
                        self.sessions[session_id]["messages"].append({
                            "role": "assistant",
                            "content": ai_response
                        })
                    
                    # Send the AI response back to the client
                    yield chatbot_pb2.ChatMessage(
                        text=ai_response,
                        sender="ai",
                        timestamp=timestamp,
                        message_id=response_id,
                        reply_to=request.message_id,
                        session_id=session_id,
                        user_id=user_id
                    )
                    
                except Exception as e:
                    logging.error(f"Error generating AI response: {str(e)}")
                    error_message = f"Sorry, I encountered an error: {str(e)}"
                    
                    # Send error message back to the client
                    yield chatbot_pb2.ChatMessage(
                        text=error_message,
                        sender="ai",
                        timestamp=timestamp,
                        message_id=response_id,
                        reply_to=request.message_id,
                        session_id=session_id,
                        user_id=user_id
                    )
            
            # Session ended normally        
            logging.info(f"Chat session {session_id} ended normally")
                    
        except Exception as e:
            logging.error(f"Error in chat session {session_id}: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Chat session error: {str(e)}")
        
        # Clean up very old sessions (could be done in a separate maintenance thread)
        self._cleanup_old_sessions()
    
    def _cleanup_old_sessions(self):
        """Clean up sessions that haven't been active for more than 24 hours"""
        current_time = datetime.now()
        with self.sessions_lock:
            sessions_to_remove = []
            for session_id, session_data in self.sessions.items():
                last_active = datetime.fromisoformat(session_data["last_active"])
                # If session is more than 24 hours old
                if (current_time - last_active).total_seconds() > 86400:  # 24 hours
                    sessions_to_remove.append(session_id)
            
            # Remove old sessions
            for session_id in sessions_to_remove:
                logging.info(f"Cleaning up inactive session {session_id}")
                del self.sessions[session_id]

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