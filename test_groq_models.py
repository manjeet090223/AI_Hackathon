
"""
Quick test to find available Groq models
"""

import os
os.environ['GROQ_API_KEY'] = 'REMOVED'

print("Testing Groq API with available models...\n")

try:
    from groq import Groq
    
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    print("✅ Groq client initialized\n")
    

    models_to_try = [
        "gemma-7b-it",
        "mixtral-8x7b-32768",
        "llama-3.1-70b-versatile",
        "llama-3.2-90b-vision-preview",
    ]
    
    for model in models_to_try:
        print(f"\nTrying model: {model}")
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": "Say 'Working' in one word."}
                ],
                max_tokens=20,
                temperature=0.2
            )
            
            print(f"  ✅ SUCCESS - Response: {response.choices[0].message.content.strip()}")
            print(f"  ✅ Use this model: {model}")
            break
            
        except Exception as e:
            error_msg = str(e)
            if "decommissioned" in error_msg:
                print(f"  ❌ Decommissioned")
            else:
                print(f"  ⚠️ Error: {error_msg[:80]}")
    
except Exception as e:
    print(f"❌ Failed: {e}")
    import traceback
    traceback.print_exc()
