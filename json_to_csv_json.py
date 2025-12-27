# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maxim Strekolovskiy

import os
import json
import csv
import asyncio
import aiohttp
import sys
from typing import Dict, Any, List, Optional
from anyio import Semaphore
from tqdm.asyncio import tqdm_asyncio
from agent import ChatGPTClassifier

# Enable ANSI/emoji support in Windows terminals (best-effort)
if sys.platform == "win32":
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    
# Configuration
MAX_CONCURRENT_REQUESTS = 10
semaphore = Semaphore(MAX_CONCURRENT_REQUESTS)

def is_user_message(event: Dict) -> bool:
    """Return True if the event looks like an end-user message (not agent/bot)."""
    if not isinstance(event, dict):
        return False
    
    text = event.get("text", "")
    agent_id = event.get("agent_id")
    bot_id = event.get("bot_id")
    
    return (
        isinstance(text, str) and
        agent_id is None and
        bot_id is None and
        text.strip() != ""
    )

def save_to_csv(result_data: Dict[str, Any], csv_path: str) -> None:
    """Save results to a CSV file."""
    rows = result_data.get("result", [])
    
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.writer(csvfile, delimiter=";")
        writer.writerow([
            "dialog_id",
            "dialog_date",
            "gpt_category",
            "gpt_sentiment",
            "question_text"
        ])
        
        for item in rows:
            if not isinstance(item, dict):
                continue
                
            writer.writerow([
                item.get("dialog_id", ""),
                item.get("dialog_date", ""),
                item.get("gpt_category", ""),
                item.get("gpt_sentiment", ""),
                item.get("question_text", "")
            ])

async def process_single_message(
    classifier: ChatGPTClassifier,
    dialog_id: str,
    dialog_date: str,
    text: str,
    pbar: tqdm_asyncio
) -> Optional[Dict]:
    """Process one message and update the progress bar."""
    try:
        # Async analysis with concurrency limits
        async with semaphore:
            analysis = await classifier.analyze_text(text)
            
            if not analysis:
                return None
                
            return {
                "dialog_id": dialog_id,
                "dialog_date": str(dialog_date),
                "question_text": text,
                "gpt_category": analysis.get("category", "Other"),
                "gpt_sentiment": analysis.get("sentiment", "neutral")
            }
            
    except Exception as e:
        print(f"Failed to process a message: {str(e)}")
        return None
    finally:
        pbar.update(1)

async def process_jivo_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Main processing pipeline for Jivo export JSON."""
    results = []

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Please set it in your environment and try again.")

    classifier = ChatGPTClassifier(api_key)
    
    if not isinstance(data, dict):
        return {"result": results}

    # Collect all end-user messages with basic type validation
    all_messages = []
    for client in data.get("clients", []):
        if not isinstance(client, dict):
            continue
            
        for chat in client.get("chats", []):
            if not isinstance(chat, dict):
                continue
                
            for event in chat.get("events", []):
                if is_user_message(event) and isinstance(event, dict):
                    all_messages.append({
                        "dialog_id": chat.get("chat_id", "N/A"),
                        "dialog_date": chat.get("started_at", "N/A"),
                        "text": event.get("text", "")
                    })

    # Process with progress bar
    with tqdm_asyncio(total=len(all_messages), desc="Analyzing messages") as pbar:
        tasks = [
            process_single_message(
                classifier,
                msg["dialog_id"],
                msg["dialog_date"],
                msg["text"],
                pbar
            )
            for msg in all_messages
        ]

        # Batch processing (50 messages per gather)
        for i in range(0, len(tasks), 50):
            batch = tasks[i:i+50]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            
            for res in batch_results:
                if isinstance(res, dict):
                    results.append(res)
                elif isinstance(res, Exception):
                    print(f"Task error: {str(res)}")

    return {"result": results}

async def download_and_process_jivo(url: str, output_json: str, output_csv: str) -> None:
    """Download Jivo export JSON and run the pipeline."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=60) as response:
                response.raise_for_status()
                data = await response.json()
                
                if not isinstance(data, dict):
                    raise ValueError("Invalid data format (expected JSON object).")
                
                result_dict = await process_jivo_data(data)
                
                # Save results
                with open(output_json, "w", encoding="utf-8") as f:
                    json.dump(result_dict, f, ensure_ascii=False, indent=2)
                    
                save_to_csv(result_dict, output_csv)
                
    except Exception as e:
        raise RuntimeError(f"Processing failed: {str(e)}")

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════╗")
    print("║             Jivo Chat Analytics              ║")
    print("╚══════════════════════════════════════════════╝")
    
    # Ask user for export URL
    while True:
        jivo_url = input("\nEnter the Jivo export JSON URL (or press Enter to exit):\n> ").strip()
        
        if not jivo_url:
            print("Exiting...")
            exit()
            
        if jivo_url.startswith(('http://', 'https://')):
            break
        print("Error: URL must start with http:// or https://")

    output_json_file = "parsed_jivo.json"
    output_csv_file = "parsed_jivo.csv"

    try:
        print("\n⏳ Starting processing...")
        asyncio.run(download_and_process_jivo(jivo_url, output_json_file, output_csv_file))
        print("\n✅ Done! Results saved to:")
        print(f"- JSON: {os.path.abspath(output_json_file)}")
        print(f"- CSV:  {os.path.abspath(output_csv_file)}")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
    finally:
        input("\nPress Enter to exit...")