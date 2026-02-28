import os
import json
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY')
)

# ==============================
# LOAD KNOWLEDGE
# ==============================
with open("minangkabau_knowledge.json", "r", encoding="utf-8") as f:
    knowledge_json = json.load(f)

def build_system_prompt():
    knowledge_data = json.dumps(knowledge_json, indent=2, ensure_ascii=False)

    return f"""
Kamu adalah AI bernama Kura yang fokus pada pelestarian bahasa Minangkabau.

Berikut adalah data referensi dalam format JSON:

{knowledge_data}

Gunakan data ini untuk menjawab pertanyaan secara akurat.
Jawab dengan bahasa Indonesia sederhana dan ramah.
Jika pertanyaan di luar topik, arahkan kembali ke bahasa Minangkabau.
"""

MODEL_NAME = "openrouter/free"

chat_history = [
    {
        "role": "system",
        "content": build_system_prompt()
    }
]

stream_mode = True


# ==============================
# SAVE CHAT HISTORY
# ==============================
def save_history_to_file(filename="chat_history.json"):
    data_to_save = chat_history[1:] if len(chat_history) > 1 else []

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, indent=2, ensure_ascii=False)

    print(f"\n[System] Chat history saved to {filename}\n")


# ==============================
# LEARN FEATURE
# ==============================
def learn_new_word(user_input):
    global knowledge_json, chat_history

    try:
        data = user_input.replace("/learn", "").strip()

        if "=" not in data:
            print("AI: Format salah. Gunakan: /learn Kata = Arti")
            return

        kata, arti = data.split("=", 1)
        kata = kata.strip()
        arti = arti.strip()

        # Tambah ke JSON
        knowledge_json["kosakata"][kata] = arti

        # Simpan permanen ke file
        with open("minangkabau_knowledge.json", "w", encoding="utf-8") as f:
            json.dump(knowledge_json, f, indent=2, ensure_ascii=False)

        # Update system prompt realtime
        chat_history[0]["content"] = build_system_prompt()

        print(f"AI: Kosakata '{kata}' berhasil ditambahkan! 🎉")

    except Exception as e:
        print("AI: Terjadi kesalahan saat belajar.")
        print(e)


# ==============================
# GET RESPONSE NORMAL
# ==============================
def get_response_normal(messages):
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.7,
    )

    return response.choices[0].message.content


# ==============================
# GET RESPONSE STREAM
# ==============================
def get_response_stream(messages):
    full_answer = ""

    stream = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.7,
        stream=True
    )

    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            print(content, end='', flush=True)
            full_answer += content

    print()
    return full_answer


# ==============================
# MAIN LOOP
# ==============================
def main():
    global stream_mode

    print(" Welcome to Your First AI Chatbot on Terminal\n")
    print("Commands:")
    print("  /stream on   -> aktifkan streaming mode")
    print("  /stream off  -> matikan streaming mode")
    print("  /save        -> simpan riwayat chat")
    print("  /learn Kata = Arti  -> ajarkan kosakata baru")
    print("  /exit        -> keluar\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() == "/exit":
            print("AI: Byee 👋")
            break

        if user_input.lower() == "/save":
            save_history_to_file()
            continue

        if user_input.lower() == "/stream on":
            stream_mode = True
            print("[System] Streaming mode: ON\n")
            continue

        if user_input.lower() == "/stream off":
            stream_mode = False
            print("[System] Streaming mode: OFF\n")
            continue

        if user_input.lower().startswith("/learn"):
            learn_new_word(user_input)
            continue

        if not user_input:
            print("[System] (kosong, ketik sesuatu atau /exit)")
            continue

        chat_history.append({
            "role": "user",
            "content": user_input
        })

        print("AI: ", end="", flush=True)

        if stream_mode:
            ai_reply = get_response_stream(chat_history)
        else:
            ai_reply = get_response_normal(chat_history)
            print(ai_reply)

        chat_history.append({
            "role": "assistant",
            "content": ai_reply
        })

        print()


if __name__ == "__main__":
    main()