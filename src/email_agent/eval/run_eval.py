import json, os, time, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from email_agent.classifier import classify_email
from email_agent.llm_client import get_default_client
from email_agent.configs import Settings, get_settings

load_dotenv()
settings: Settings = get_settings()

def run_eval(test_file: str = settings.email_test_file):
    with open(test_file) as f:
        test_cases = json.load(f)
        
    llm = get_default_client()
    
    correct = 0
    results = []
    confusions = []
    
    for case in test_cases:
        classification = classify_email(
            llm, sender=case["sender"], subject=case["subject"], body=case["body"]
        )
        is_correct = classification.category.value == case["expected_category"]
        correct += int(is_correct)
        results.append(
            {
                "subject": case["subject"],
                "expected": case["expected_category"],
                "predicted": classification.category.value,
                "confidence": classification.confidence,
                "correct": is_correct,
            }
        )
        if not is_correct:
            confusions.append(results[-1])
        time.sleep(3)
    
    accuracy = correct / len(test_cases) if test_cases else 0.0
    
    print(f"\n{'='*60}")
    print(f"Accuracy: {correct}/{len(test_cases)} ({accuracy:.1%})")
    print(f"\n{'='*60}")
    
    if confusions:
        print("Misclassifications:")
        for c in confusions:
            print(f"  '{c['subject'][:50]}'")
            print(f"   expected: {c['expected']}  |  got: {c['predicted']} (conf {c['confidence']:.2f})")
    else:
        print("No misclassifications on this run.")

    return accuracy, results

if __name__ == "__main__":
    run_eval()