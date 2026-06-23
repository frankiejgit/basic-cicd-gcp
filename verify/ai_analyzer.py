import os
from google import genai

print("Fetching recent logs and error rates for the 10% Canary Revision...")
# In a production scenario, you would query the Cloud Monitoring API here.
# For this live demo, we pass simulated telemetry.
error_rate = 0.5 
latency_ms = 120

print("Sending telemetry to Vertex AI (Gemini) for Canary Analysis...")
prompt = f"""
You are an expert Site Reliability Engineer. 
The new canary deployment has an error rate of {error_rate}% and a latency of {latency_ms}ms. 
Our SLA allows up to a 1% error rate and 200ms latency. 
Analyze these metrics. Is it safe to promote this deployment to 100% of users? 
Reply STRICTLY with the word PASS or FAIL.
"""

# Initialize the official Google GenAI SDK
client = genai.Client(vertexai=True, location="us-central1")

try:
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    decision = response.text.strip().upper()
    
    print(f"AI Decision: {decision}")

    if "PASS" in decision:
        print("Canary is healthy! Instructing Cloud Deploy to promote to 100%.")
        exit(0) # Exit 0 tells Cloud Deploy to continue the rollout
    else:
        print("Canary is unhealthy :'( Instructing Cloud Deploy to halt and rollback.")
        exit(1) # Exit 1 tells Cloud Deploy to fail the pipeline
        
except Exception as e:
    print(f"Error calling Vertex AI: {e}")
    exit(1)