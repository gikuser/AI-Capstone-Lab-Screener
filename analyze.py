import json
import os
from collections import Counter

def analyze_feedback():
    log_file = 'feedback_log.json'
    
    if not os.path.exists(log_file):
        print("\n[!] No feedback log found. Run the app and submit feedback first.")
        return

    try:
        with open(log_file, 'r') as f:
            logs = json.load(f)
    except Exception as e:
        print(f"[!] Error reading logs: {e}")
        return

    total_responses = len(logs)
    negative_feedback = [log for log in logs if log.get('feedback') == 'bad']
    total_negative = len(negative_feedback)
    
    # Extract query text for "failed" queries
    failed_queries = [log.get('user_input', 'Unknown') for log in negative_feedback]
    query_counts = Counter(failed_queries)
    top_3_failed = query_counts.most_common(3)

    print("\n" + "="*40)
    print("      AGENTIC AI SYSTEM: AUDIT REPORT")
    print("="*40)
    print(f"Total Interactions:      {total_responses}")
    print(f"Negative Feedback:       {total_negative}")
    print(f"Positive Feedback:       {total_responses - total_negative}")
    
    if total_responses > 0:
        satisfaction = ((total_responses - total_negative) / total_responses) * 100
        print(f"Customer Satisfaction:   {satisfaction:.1f}%")
    
    print("-" * 40)
    print("TOP 3 FAILED QUERIES (Negative Feedback)")
    if top_3_failed:
        for i, (query, count) in enumerate(top_3_failed, 1):
            # Truncate long queries for display
            display_query = (query[:70] + '...') if len(query) > 70 else query
            print(f"{i}. [{count} times] {display_query}")
    else:
        print("None recorded yet.")
    print("=" * 40 + "\n")

if __name__ == "__main__":
    analyze_feedback()
